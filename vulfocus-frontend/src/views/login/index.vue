<template>
  <div class="login-container">
    <div class="icon-con" style="float: right;margin-top: 0px" >
      <a href="https://github.com/fofapro/vulfocus" target="_blank" class="github-corner" aria-label="View source on Github">
        <svg
          width="80"
          height="80"
          viewBox="0 0 250 250"
          style="fill:#40c9c6; color:#fff;"
          aria-hidden="true"
          position="relative"
        >
          <path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z" />
          <path
            d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2"
            fill="currentColor"
            style="transform-origin: 130px 106px;"
            class="octo-arm"
          />
          <path
            d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z"
            fill="currentColor"
            class="octo-body"
          />
        </svg>
      </a >
    </div>
    <div class="form-container">
      <el-form ref="loginForm" :model="loginForm" :rules="loginRules" class="login-form" auto-complete="on" label-position="left">
        <div class="title-container" align="center" style="margin-bottom: 10%;">
          <img src="../../assets/logintitle.png" style="margin-top: 30px"/>
        </div>
        <el-form-item prop="username" style="margin-left: 45px;margin-right: 40px">
<!--          <span class="svg-container">-->
<!--            <svg-icon icon-class="user" />-->
<!--          </span>-->
          <el-input
            ref="username"
            v-model="loginForm.username"
            placeholder="Username"
            name="username"
            type="text"
            tabindex="1"
            auto-complete="on"
          />
        </el-form-item>
        <el-form-item prop="password" style="margin-left: 45px;margin-right: 40px">
<!--          <span class="svg-container">-->
<!--            <svg-icon icon-class="password" />-->
<!--          </span>-->
          <el-input
            :key="passwordType"
            ref="password"
            v-model="loginForm.password"
            :type="passwordType"
            placeholder="Password"
            name="password"
            tabindex="2"
            auto-complete="on"
            @keyup.enter.native="handleLogin"
          />
          <span class="show-pwd" @click="showPwd">
            <svg-icon :icon-class="passwordType === 'password' ? 'eye' : 'eye-open'" />
          </span>
        </el-form-item>
        <div align="center">
          <el-button :loading="loading" type="primary" style="width:75%;margin-bottom:30px;margin-left: 10px" @click.native.prevent="handleLogin">登入</el-button>
          <el-button  style="width:75%;margin-bottom:30px;" @click="jumpreg" >注册</el-button>
        </div>
        <div>
          <el-button type="text" @click="findPassword" style="color: #009ad6;margin-left: 70%">忘记密码
            <i class="el-icon-question"></i>
          </el-button>
        </div>
      </el-form>
      <el-dialog :visible.sync="updateDialogVisible" style="width: 26%;height: 45%;margin: auto" :fullscreen="true" title="密码找回" :destroy-on-close="true" :close-on-click-modal="false" :close-on-press-escape="false">
        <el-form :model="ruleForm" :inline="true"  class="confirm-from" status-icon :rules="rules" ref="ruleForm" auto-complete="on" label-position="left" >
          <el-form-item>
            <el-input
                ref="username"
                placeholder="请输入要找回的账号"
                v-model="ruleForm.username"
                name="username"
                type="text"
                style="width:70%"
              />
          </el-form-item>
          <el-form-item style="margin-top: 5px">
            <el-button @click="handleSendMail">发送邮件</el-button>
          </el-form-item>
          <el-form-item>
            <el-input
                placeholder="输入邮箱验证码"
                v-model="ruleForm.auth"
                type="text"
                style="width:70%"
              />
          </el-form-item>
          <el-form-item prop="pass">
            <el-input
                placeholder="输入新密码"
                v-model="ruleForm.pass"
                type="password"
                style="width:70%"
                autocomplete="off"
              />
          </el-form-item>
          <el-form-item prop="checkPass">
            <el-input
                placeholder="确认密码"
                v-model="ruleForm.checkPass"
                type="password"
                style="width:70%"
                autocomplete="off"
              />
          </el-form-item>
          <el-form-item style="margin-top: 5px">
            <el-button type="primary" @click="handleConfirm">提交</el-button>
          </el-form-item>
        </el-form>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import { lininfo } from "@/api/docker"
import { sendMail,valMail } from "@/api/user"

export default {
  name: 'Login',
  data() {
    const validatePass = (rule, value, callback) => {
        if (value === '') {
          callback(new Error('请输入密码'));
        } else {
          if (this.ruleForm.checkPass !== '') {
            this.$refs.ruleForm.validateField('checkPass');
          }
          callback();
        }
      };
    const validatePass2 = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'));
      } else if (value !== this.ruleForm.pass) {
        callback(new Error('两次输入密码不一致!'));
      } else {
        callback();
      }
    };
    const validatePassword = (rule, value, callback) => {
      if (value.length < 1) {
        callback(new Error('The password can not be less than 6 digits'))
      } else {
        callback()
      }
    }
    return {
      loginForm: {
        username: '',
        password: ''
      },
      loginRules: {
        password: [{ required: true, trigger: 'blur', validator: validatePassword }]
      },
      loading: false,
      passwordType: 'password',
      redirect: undefined,
      updateDialogVisible: false,
      ruleForm: {
        username: '',
        auth: '',
        pass:'',
        checkPass:''
      },
      rules: {
        pass: [
          { validator: validatePass, trigger: 'blur' }
        ],
        checkPass: [
          { validator: validatePass2, trigger: 'blur' }
        ],
      },
      displayInput:false
    }
  },
  watch: {
    $route: {
      handler: function(route) {
        this.redirect = route.query && route.query.redirect
      },
      immediate: true
    }
  },
  methods: {
    jumpreg(){
      this.$router.push('/register')
    },
    showPwd() {
      if (this.passwordType === 'password') {
        this.passwordType = ''
      } else {
        this.passwordType = 'password'
      }
      this.$nextTick(() => {
        this.$refs.password.focus()
      })
    },
    findPassword(){
      this.updateDialogVisible = true
    },
    handleConfirm(){
      let code = this.ruleForm.auth
      this.$refs.ruleForm.validate(valid => {
        if (valid){
          if (code){
            valMail(this.ruleForm).then(response=>{
            let data = response.data
            if (data.code===200){
              this.$message({
              message: '密码找回成功',
              type: "success",
              })
              this.updateDialogVisible = false
            }else {
              this.$message({
              message: data.msg,
              type: "error",
            })
          }
        })
      }else {
            this.$message({
              message: "验证码不能为空",
              type: "error",
            })
          }
        }else {
          return false
        }
      })
    },
    handleSendMail(){
      sendMail(this.ruleForm).then(response =>{
        let data = response.data
        if (data.code===200){
          this.$message({
                message:  "成功发送",
                type: "success",
              })
        } else {
          this.$message({
            message: data.msg,
            type: "error",
          })
        }
      })
    },
    handleLogin() {
      this.$refs.loginForm.validate(valid => {
        if (valid) {
          this.loading = true
          this.$store.dispatch('user/login', this.loginForm).then(() => {
            this.$router.push({ path: this.redirect || '/' })
            this.loading = false
            lininfo()
          }).catch(() => {
            this.loading = false
          })
        } else {
          return false
        }
      })
    },



  }
}
</script>

<style lang="scss">
/* 修复input 背景不协调 和光标变色 */
/* Detail see https://github.com/PanJiaChen/vue-element-admin/pull/927 */

$bg:#283443;
$light_gray:#aaa;
$cursor: #fff;

@supports (-webkit-mask: none) and (not (cater-color: $cursor)) {
  .login-container .el-input input {
    color: $cursor;
  }
}

/* reset element-ui css */
.login-container {
  .el-input {
    display: inline-block;
    height: 48px;
    width: 332px;

    input {
      background: transparent;
      border: 0px;
      -webkit-appearance: none;
      border-radius: 0px;
      padding: 12px 5px 12px 15px;
      color: $light_gray;
      height: 48px;
      width: 332px;
      caret-color: $cursor;

      &:-webkit-autofill {
        box-shadow: 0 0 0px 1000px $bg inset !important;
        -webkit-text-fill-color: $cursor !important;
      }
    }
  }
  /*.el-dialog__header{*/
  /*  background-color: #3d7ed5;*/
  /*}*/
  /*.el-dialog__body{*/
  /*  background-color: #3d7ed5;*/
  /*}*/

  .el-form-item {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.1);
    border-radius: 5px;
    color: #454545;
  }
}
</style>

<style lang="scss" scoped>

$bg:#2d3a4b;
$dark_gray:#889aa4;
$light_gray:#eee;
.form-container{
  .login-form {
    position: relative;
    width: 400px;
    height: 470px;
    max-width: 80%;
    /*padding: 120px 35px 0;*/
    margin: 150px;
    overflow: hidden;
    float:right;
    background-image: url("../../assets/loginl.png");
    background-size: 100% 100%;
  }

  .tips {
    font-size: 14px;
    color: #fff;
    margin-bottom: 10px;

    span {
      &:first-of-type {
        margin-right: 16px;

      }
    }
  }

  .svg-container {
    padding: 6px 5px 6px 15px;
    color: $dark_gray;
    vertical-align: middle;
    width: 48px;
    display: inline-block;
  }

  .title-container {
    position: relative;

    .title {
      font-size: 26px;
      color: $light_gray;
      margin: 0px auto 45px auto;
      text-align: center;
      font-weight: bold;
    }
  }

  .show-pwd {
    position: absolute;
    right: 10px;
    top: 7px;
    font-size: 16px;
    color: $dark_gray;
    cursor: pointer;
    user-select: none;
  }
}
.login-container {
  min-height: 100%;
  height: 100%;
  width: 100%;
  background-color: $bg;
  overflow: hidden;
  background: url("../../assets/loginbackground.png") center no-repeat;
  background-size: 100%;
}
</style>
<style>

</style>
