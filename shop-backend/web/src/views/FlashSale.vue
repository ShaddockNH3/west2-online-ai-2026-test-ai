<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NInputNumber,
  NModal,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../api";
import { flashText, flashType } from "../theme";
import { store } from "../store";

const router = useRouter();
const message = useMessage();

const loading = ref(false);
const activities = ref([]);
const myRequests = ref([]);
const addresses = ref([]);

const buyVisible = ref(false);
const buyTarget = ref(null);
const buySku = ref(null);
const quantity = ref(1);
const addressId = ref(null);
const buying = ref(false);
const currentTicket = ref(null);
const currentStatus = ref("");

const addressOptions = computed(() =>
  addresses.value.map((item) => ({
    label: `${item.receiver} · ${item.phone} · ${item.detail}`,
    value: item.id,
  })),
);

async function load() {
  loading.value = true;
  try {
    const data = await http.get("/activities");
    activities.value = data.items.filter((item) => item.type === "FLASH_SALE" && item.running);
    if (store.user) {
      const [requests, addressData] = await Promise.all([
        http.get("/flash-sale/requests").catch(() => ({ items: [] })),
        http.get("/addresses").catch(() => ({ items: [] })),
      ]);
      myRequests.value = requests.items;
      addresses.value = addressData.items;
      const preferred = addresses.value.find((item) => item.isDefault) || addresses.value[0];
      addressId.value = addressId.value || preferred?.id || null;
    }
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

function openBuy(activity, sku) {
  if (!store.user) {
    router.push({ name: "login", query: { redirect: "/flash" } });
    return;
  }
  if (!addresses.value.length) {
    message.warning("先添加一条收货地址");
    router.push("/addresses");
    return;
  }
  buyTarget.value = activity;
  buySku.value = sku;
  quantity.value = 1;
  buyVisible.value = true;
}

async function submitBuy() {
  buying.value = true;
  const requestId = `flash-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  try {
    const ticket = await http.post(`/activities/${buyTarget.value.id}/flash-sale`, {
      skuId: buySku.value.skuId,
      quantity: quantity.value,
      addressId: addressId.value,
      requestId,
    });
    currentTicket.value = ticket;
    currentStatus.value = ticket.status;
    buyVisible.value = false;
    message.success("抢购请求已受理，正在排队建单");
    await poll(requestId);
  } catch (error) {
    message.error(error.message);
  } finally {
    buying.value = false;
  }
}

async function poll(requestId) {
  for (let index = 0; index < 20; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    try {
      const ticket = await http.get(`/flash-sale/requests/${requestId}`);
      currentTicket.value = ticket;
      currentStatus.value = ticket.status;
      if (ticket.status !== "QUEUED") break;
    } catch {
      break;
    }
  }
  await load();
}

function remaining(sku) {
  if (sku.saleQuota === null) return "不限量";
  return `剩 ${Math.max(0, sku.saleQuota - sku.soldCount)} 件`;
}

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">限量抢购</h1>
        <p class="page-sub">
          抢购接口先占用库存并立即返回 ticket，建单由后台任务完成；结果页会自己刷新。
        </p>
      </div>
      <n-button @click="load">刷新</n-button>
    </div>

    <n-alert v-if="currentTicket" :type="currentStatus === 'SUCCEEDED' ? 'success' : currentStatus === 'FAILED' ? 'error' : 'info'" style="margin-bottom: 16px">
      <div class="row-between">
        <div>
          抢购结果：<strong>{{ flashText[currentStatus] || currentStatus }}</strong>
          <span v-if="currentTicket.orderNo"> · 订单 {{ currentTicket.orderNo }}</span>
          <span v-else-if="currentTicket.message"> · {{ currentTicket.message }}</span>
        </div>
        <n-button
          v-if="currentTicket.orderNo"
          size="small"
          type="primary"
          @click="router.push('/orders')"
        >
          去支付
        </n-button>
      </div>
    </n-alert>

    <n-spin :show="loading">
      <div v-if="activities.length" class="stack">
        <n-card v-for="activity in activities" :key="activity.id" :title="activity.name">
          <template #header-extra>
            <n-tag type="error" :bordered="false" size="small">进行中</n-tag>
          </template>
          <p class="muted desc">{{ activity.description || "限量发售，售完即止" }}</p>
          <div class="sku-grid">
            <div v-for="sku in activity.skus" :key="sku.skuId" class="sku-card">
              <div class="sku-name">{{ sku.skuCode }}</div>
              <div class="muted small">{{ remaining(sku) }}</div>
              <div class="sku-price">
                <span class="price">{{ money(sku.activityPrice) }}</span>
                <span class="muted strike">{{ money(sku.originalPrice) }}</span>
              </div>
              <div v-if="sku.perUserLimit" class="muted small">每人限购 {{ sku.perUserLimit }} 件</div>
              <n-button
                type="primary"
                size="small"
                block
                :disabled="sku.saleQuota !== null && sku.soldCount >= sku.saleQuota"
                @click="openBuy(activity, sku)"
              >
                {{ sku.saleQuota !== null && sku.soldCount >= sku.saleQuota ? "已售罄" : "立即抢购" }}
              </n-button>
            </div>
          </div>
        </n-card>
      </div>
      <n-empty v-else description="当前没有进行中的限量活动" class="empty" />
    </n-spin>

    <n-card v-if="myRequests.length" title="我的抢购记录" style="margin-top: 20px">
      <div v-for="item in myRequests" :key="item.requestId" class="request-row">
        <div>
          <div class="req-name">{{ item.activityName }}</div>
          <div class="muted small">
            {{ money(item.unitPrice) }} × {{ item.quantity }} · {{ item.requestId }}
          </div>
        </div>
        <div class="row-end">
          <n-tag size="small" :type="flashType[item.status] || 'default'" :bordered="false">
            {{ flashText[item.status] || item.status }}
          </n-tag>
          <span v-if="item.orderNo" class="muted small">{{ item.orderNo }}</span>
        </div>
      </div>
    </n-card>

    <n-modal v-model:show="buyVisible" preset="card" title="确认抢购" style="width: 440px">
      <div v-if="buySku" class="buy-body">
        <div class="row-between">
          <span>{{ buyTarget?.name }}</span>
          <span class="price">{{ money(buySku.activityPrice) }}</span>
        </div>
        <div class="muted small">{{ buySku.skuCode }} · {{ remaining(buySku) }}</div>
        <div class="buy-field">
          <div class="field-label">数量</div>
          <n-input-number v-model:value="quantity" :min="1" :max="buySku.perUserLimit || 10" />
        </div>
        <div class="buy-field">
          <div class="field-label">收货地址</div>
          <n-select v-model:value="addressId" :options="addressOptions" placeholder="选择地址" />
        </div>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="buyVisible = false">取消</n-button>
          <n-button type="primary" :loading="buying" @click="submitBuy">提交抢购</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.desc {
  margin: 0 0 14px;
  font-size: 13px;
}

.sku-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.sku-card {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fbfcff;
}

.sku-name {
  font-weight: 600;
  font-size: 13px;
}

.sku-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.strike {
  font-size: 12px;
  text-decoration: line-through;
}

.small {
  font-size: 12px;
}

.request-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--line);
}

.req-name {
  font-weight: 500;
}

.row-end {
  display: flex;
  align-items: center;
  gap: 8px;
}

.buy-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.buy-field {
  margin-top: 8px;
}

.field-label {
  font-size: 12px;
  color: #334155;
  margin-bottom: 6px;
}
</style>
