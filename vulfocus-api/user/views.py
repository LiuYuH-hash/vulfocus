from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse,HttpResponse
from rest_framework import viewsets,mixins
from user.serializers import UserProfileSerializer, User, UserRegisterSerializer,UpdatePassSerializer,LoginSerializer
from user.serializers import SendEmailSerializer,ResetPasswordSerializer
from rest_framework.views import APIView
from django.contrib.auth import logout, login, authenticate
from user.permissions import IsOwner
from django.views.generic.base import View
from user.models import UserProfile, EmailCode
from django.core.mail import send_mail
from rest_framework import permissions
from vulfocus.settings import EMAIL_FROM
from dockerapi.common import R
from dockerapi.models import ContainerVul
from vulfocus.settings import REDIS_IMG as r_img
from PIL import ImageDraw,ImageFont,Image
import random
import io
import datetime
from user.utils import generate_code
from time import sleep
import uuid
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.utils import jwt_response_payload_handler
from rest_framework.response import Response
from datetime import datetime, timedelta
from rest_framework_jwt.settings import  api_settings



class ListAndUpdateViewSet(mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides default `update()`, `list()`actions.
    """
    pass


class UserSet(ListAndUpdateViewSet):
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return UserProfile.objects.all()
        else:
            return UserProfile.objects.all()

    def update(self, request, *args, **kwargs):
        user = request.user
        if not user.is_superuser:
            return JsonResponse(R.build(msg="权限不足"))
        new_pwd = request.data.get("pwd", "")
        new_pwd = new_pwd.strip()
        if len(new_pwd) < 6:
            return JsonResponse(R.build(msg="密码格式不正确"))
        user_info = self.get_object()
        user_info.set_password(new_pwd)
        user_info.save()
        return JsonResponse(R.ok())


class get_user_rank(APIView):

    def get(self, request):
        page_no = int(request.GET.get("page", 1))
        score_list = ContainerVul.objects.filter(is_check=True, time_model_id='').values('user_id').annotate(
            score=Sum("image_id__rank")).values('user_id', 'score').order_by("-score")
        try:
            pages = Paginator(score_list, 20)
            page = pages.page(page_no)
        except Exception as e:
            return JsonResponse(R.err())
        result = []
        for _data in list(page):
            user_info = UserProfile.objects.filter(id=_data["user_id"]).first()
            username = ""
            if user_info:
                username = user_info.username
            result.append({"rank": _data["score"], "name": username})
        data = {
            'results': result,
            'count': len(score_list)
        }
        return JsonResponse(R.ok(data=data))


class get_user_info(APIView):
    def get(self, request):
        user_info = User.objects.get(pk=request.user.id)
        serializer = UserProfileSerializer(user_info)
        return JsonResponse(serializer.data)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return JsonResponse({"msg": "OK"})


class UserRegView(viewsets.mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = UserProfile.objects.all()
    serializer_class = UserRegisterSerializer


# 定义一验证码
class MyCode(View):

    # 定义一个随机验证颜色
    def get_random_color(self):
        R = random.randrange(255)
        G = random.randrange(255)
        B = random.randrange(255)
        return (R,G,B)
    # 随机验证码
    def get(self,request):
        img_size = (110,50)
        image = Image.new('RGB',img_size,'#27408B')
        draw = ImageDraw.Draw(image,'RGB')
        source = '0123456789abcdefghijklmnopqrstevwxyz'
        code_str = ''
        for i in range(4):
            text_color = self.get_random_color()
            tmp_num = random.randrange(len(source))
            random_str = source[tmp_num]
            code_str +=random_str
            draw.text((10+30*i,20),random_str,text_color,)
        buf = io.BytesIO()
        image.save(buf, 'png')
        data = buf.getvalue()
        if "HTTP_X_REAL_IP" in request.META:
            ip = request.META.get("HTTP_X_REAL_IP")
        else:
            ip = request.META.get("REMOTE_ADDR")
        if ip == "127.0.0.1":
            return HttpResponse(data, 'image/png')
        r_img.sadd(ip, code_str)
        r_img.expire(ip, 60)
        return HttpResponse(data, 'image/png')


class UpdatePassViewset(mixins.UpdateModelMixin,viewsets.GenericViewSet):
    serializer_class = UpdatePassSerializer
    permission_classes = [permissions.IsAuthenticated,IsOwner]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):

        password = request.data["pass"]
        checkPassword = request.data["checkPass"]
        if password != checkPassword:
            return JsonResponse({
                "code": 401,
                "msg": "两次密码不一致"
            })
        user = self.request.user
        user.set_password(raw_password=checkPassword)
        user.save()
        return JsonResponse({"code": 200, "msg": "修改密码成功"})


#自定义登录
class LoginViewset(mixins.CreateModelMixin,viewsets.GenericViewSet):
    serializer_class = LoginSerializer
    queryset = User.objects.all()
    permission_classes = []
    authentication_classes = ()
    def create(self, request, *args, **kwargs):
        username = request.data["username"]
        password = request.data["password"]
        #code=request.data["code"]
        user=User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"code": 400, "msg": "用户名错误"})
        if not user.check_password(password):
            return JsonResponse({"code": 400, "msg": "密码错误"})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user=authenticate(username=username,password=password)
        login(request,user)
        #采用jwt模式认证
        serializer_instance=JSONWebTokenSerializer(data=request.data)
        if serializer_instance.is_valid():
            user = serializer_instance.object.get('user') or request.user
            token = serializer_instance.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            return response
        return JsonResponse({"code": "400", "msg": "error"}, status=200)



class SendEmailViewset(mixins.CreateModelMixin,viewsets.GenericViewSet):
    serializer_class = SendEmailSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data.get("username", None)
        if not User.objects.filter(username=username).count():
            return JsonResponse({"code": 400, "msg": "该用户不存在"})
        user = User.objects.get(username=username)
        one_minute_ago = datetime.now()-timedelta(minutes=1)
        if EmailCode.objects.filter(user=user, add_time__gt=one_minute_ago).count():
            return JsonResponse({"code": 400, "msg": "距离上次发送未超过一分钟"})
        code = generate_code()
        #判断数据库中是否有相同的验证码记录
        while EmailCode.objects.filter(code=code).count():
            code = generate_code()
        email_instance = EmailCode(user=user, code=code, email=user.email)
        send_mail(subject="找回密码", message="您的验证码是%s,有效期为2分钟"%(code), from_email=EMAIL_FROM, recipient_list=[user.email])
        email_instance.save()
        return JsonResponse({"code": 200, "msg": "ok"})



#重置密码
class ResetPasswordViewset(mixins.UpdateModelMixin,viewsets.GenericViewSet):
    serializer_class = ResetPasswordSerializer
    permission_classes = []

    def get_object(self):
        code = self.request.data["auth"]
        try:
            email_instance = EmailCode.objects.filter(code=code).first()
            return email_instance.user
        except:
            return None

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        code = request.data["auth"]
        if not EmailCode.objects.filter(code=code).count():
            return JsonResponse({"code": "400", "msg": "验证码错误"})
        email_instance = EmailCode.objects.get(code=code)
        user=email_instance.user
        two_minutes_ago = datetime.now() - timedelta(minutes=2)
        if email_instance.add_time <= two_minutes_ago:
            return JsonResponse({"code": 400, "msg": "验证码已过期"})
        password = request.data['pass']
        checkPassword = request.data['checkPass']
        if password != checkPassword:
            return JsonResponse({"code": 400, "msg": "两次输入的密码不一致"})
        user.set_password(request.data["checkPass"])
        user.save()
        return JsonResponse({"code": 200, "msg": "找回成功"})
