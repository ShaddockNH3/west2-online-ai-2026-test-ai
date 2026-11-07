<script setup>
import { computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { NAvatar, NBadge, NButton, NDropdown, NIcon, NMenu } from "naive-ui";
import {
  BagHandleOutline,
  CartOutline,
  PersonCircleOutline,
  StorefrontOutline,
} from "@vicons/ionicons5";
import { http } from "../api";
import { refreshCart, signOut, store, syncUser } from "../store";

const route = useRoute();
const router = useRouter();

const menuOptions = computed(() => {
  const items = [
    { label: "全部商品", key: "/" },
    { label: "限量抢购", key: "/flash" },
    { label: "购物车", key: "/cart" },
    { label: "我的订单", key: "/orders" },
    { label: "收货地址", key: "/addresses" },
  ];
  if (store.user?.role === "ADMIN") {
    items.push({ label: "店主后台", key: "/admin" });
  }
  return items;
});

const activeKey = computed(() => {
  if (route.path.startsWith("/products")) return "/";
  return route.path;
});

const userOptions = [
  { label: "我的订单", key: "orders" },
  { label: "收货地址", key: "addresses" },
  { type: "divider", key: "d1" },
  { label: "退出登录", key: "logout" },
];

function onMenu(key) {
  router.push(key);
}

async function onUserSelect(key) {
  if (key === "orders") router.push("/orders");
  if (key === "addresses") router.push("/addresses");
  if (key === "logout") {
    try {
      await http.post("/auth/logout", {});
    } catch {
      // 退出失败也清本地，避免卡在旧 token 上
    }
    signOut();
    router.push("/login");
  }
}

onMounted(async () => {
  syncUser();
  await refreshCart();
});

watch(
  () => route.fullPath,
  async () => {
    syncUser();
    await refreshCart();
  },
);
</script>

<template>
  <div class="shell">
    <header class="header">
      <div class="header-inner">
        <div class="brand" @click="router.push('/')">
          <div class="brand-mark">
            <n-icon size="22" color="#ffffff"><storefront-outline /></n-icon>
          </div>
          <div>
            <div class="brand-name">西二小店</div>
            <div class="brand-sub">工作室周边 · 内测版</div>
          </div>
        </div>

        <n-menu
          mode="horizontal"
          :options="menuOptions"
          :value="activeKey"
          :responsive="true"
          @update:value="onMenu"
        />

        <div class="header-actions">
          <n-badge :value="store.cartCount" :max="99" :show="store.cartCount > 0">
            <n-button quaternary circle @click="router.push('/cart')">
              <template #icon>
                <n-icon><cart-outline /></n-icon>
              </template>
            </n-button>
          </n-badge>

          <template v-if="store.user">
            <n-dropdown :options="userOptions" trigger="click" @select="onUserSelect">
              <div class="user-chip">
                <n-avatar round :size="28" color="#1d4ed8">
                  {{ (store.user.nickname || store.user.username || "U").slice(0, 1) }}
                </n-avatar>
                <span class="user-name">{{ store.user.nickname || store.user.username }}</span>
              </div>
            </n-dropdown>
          </template>
          <n-button v-else type="primary" @click="router.push('/login')">登录 / 注册</n-button>
        </div>
      </div>
    </header>

    <main>
      <router-view />
    </main>

    <footer class="footer">
      <div>西二在线工作室 · 后端考核项目（第二至第四轮）</div>
      <div class="footer-sub">金额、库存与优惠均由服务端计算，前端只负责展示</div>
    </footer>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
}

.header-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  min-width: 168px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1d4ed8, #0f2f7a);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(29, 78, 216, 0.24);
}

.brand-name {
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 0.4px;
}

.brand-sub {
  font-size: 11px;
  color: var(--muted);
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: 999px;
  border: 1px solid var(--line);
  cursor: pointer;
  background: #fff;
}

.user-name {
  font-size: 13px;
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.footer {
  margin-top: auto;
  padding: 22px 20px 28px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  border-top: 1px solid var(--line);
  background: #fff;
}

.footer-sub {
  margin-top: 4px;
  color: #94a3b8;
}
</style>
