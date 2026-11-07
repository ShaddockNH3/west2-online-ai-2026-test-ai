<script setup>
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  NAlert,
  NButton,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSpace,
  useMessage,
} from "naive-ui";
import { http, saveAuth } from "../api";
import { refreshCart, syncUser } from "../store";

const router = useRouter();
const route = useRoute();
const message = useMessage();

const mode = ref("login");
const loading = ref(false);
const errorText = ref("");
const form = ref({ username: "demo", password: "demo123456", nickname: "" });

const isRegister = computed(() => mode.value === "register");

function validate() {
  if (!/^[A-Za-z0-9_]{3,32}$/.test(form.value.username)) {
    return "用户名需为 3-32 位字母、数字或下划线";
  }
  const password = form.value.password;
  if (password.length < 8 || password.length > 64) {
    return "密码长度需在 8 到 64 位之间";
  }
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    return "密码需同时包含字母和数字";
  }
  return "";
}

async function submit() {
  errorText.value = "";
  const invalid = validate();
  if (invalid) {
    errorText.value = invalid;
    return;
  }
  loading.value = true;
  try {
    if (isRegister.value) {
      await http.post("/auth/register", {
        username: form.value.username,
        password: form.value.password,
        nickname: form.value.nickname || undefined,
      });
      message.success("注册成功，正在登录");
    }
    const data = await http.post("/auth/login", {
      username: form.value.username,
      password: form.value.password,
    });
    saveAuth(data);
    syncUser();
    await refreshCart();
    message.success(`欢迎回来，${data.user.nickname || data.user.username}`);
    router.push(route.query.redirect || "/");
  } catch (error) {
    errorText.value = error.message;
  } finally {
    loading.value = false;
  }
}

function fill(username, password) {
  mode.value = "login";
  form.value.username = username;
  form.value.password = password;
}
</script>

<template>
  <div class="page login-page">
    <div class="intro">
      <div class="intro-tag">WEST2 ONLINE · SHOP</div>
      <h1>工作室周边<br />一次买齐</h1>
      <p>
        文化衫、帆布袋、徽章都在这里。下单、支付、发货、收货，一条链路走完；
        限量款单独开一场，手慢无。
      </p>
      <ul class="feature-list">
        <li>双 Token 登录，退出即失效</li>
        <li>活动价由服务端算，订单价格快照</li>
        <li>库存占用与释放全程可查</li>
      </ul>
      <div class="demo-box">
        <div>演示账号</div>
        <n-space>
          <n-button size="small" secondary @click="fill('demo', 'demo123456')">
            普通用户 demo
          </n-button>
          <n-button size="small" secondary @click="fill('admin', 'admin123456')">
            管理员 admin
          </n-button>
        </n-space>
      </div>
    </div>

    <n-card class="form-card">
      <div class="form-head">
        <h2>{{ isRegister ? "注册新账号" : "登录" }}</h2>
        <n-radio-group v-model:value="mode" size="small">
          <n-radio-button value="login">登录</n-radio-button>
          <n-radio-button value="register">注册</n-radio-button>
        </n-radio-group>
      </div>

      <n-form label-placement="top" @keyup.enter="submit">
        <n-form-item label="用户名">
          <n-input v-model:value="form.username" placeholder="3-32 位字母、数字或下划线" />
        </n-form-item>
        <n-form-item v-if="isRegister" label="昵称（可选）">
          <n-input v-model:value="form.nickname" placeholder="想让大家怎么称呼你" />
        </n-form-item>
        <n-form-item label="密码">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="至少 8 位，字母加数字"
          />
        </n-form-item>

        <n-alert v-if="errorText" type="error" :show-icon="false" class="form-error">
          {{ errorText }}
        </n-alert>

        <n-button type="primary" block size="large" :loading="loading" @click="submit">
          {{ isRegister ? "注册并登录" : "登录" }}
        </n-button>
      </n-form>

      <p class="form-note">
        注册默认是普通用户，管理员只能由初始化脚本创建，接口不接受提权参数。
      </p>
    </n-card>
  </div>
</template>

<style scoped>
.login-page {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 32px;
  align-items: center;
  min-height: calc(100vh - 220px);
}

.intro {
  padding: 36px;
  border-radius: 18px;
  background: linear-gradient(135deg, #0f2f7a 0%, #1d4ed8 62%, #3b82f6 100%);
  color: #f8fafc;
  box-shadow: 0 24px 48px rgba(15, 47, 122, 0.22);
}

.intro-tag {
  font-size: 11px;
  letter-spacing: 3px;
  opacity: 0.72;
}

.intro h1 {
  margin: 14px 0 12px;
  font-size: 34px;
  line-height: 1.3;
  font-weight: 700;
}

.intro p {
  margin: 0;
  line-height: 1.8;
  font-size: 14px;
  color: rgba(248, 250, 252, 0.86);
}

.feature-list {
  margin: 22px 0 26px;
  padding-left: 18px;
  font-size: 13px;
  line-height: 2;
  color: rgba(248, 250, 252, 0.82);
}

.demo-box {
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
}

.demo-box > div {
  margin-bottom: 8px;
  opacity: 0.8;
}

.form-card {
  max-width: 420px;
  width: 100%;
  justify-self: end;
}

.form-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.form-head h2 {
  margin: 0;
  font-size: 20px;
}

.form-error {
  margin-bottom: 14px;
}

.form-note {
  margin: 16px 0 0;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.7;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .form-card {
    justify-self: stretch;
    max-width: none;
  }
}
</style>
