<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NAlert,
  NButton,
  NCard,
  NEmpty,
  NInput,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../api";
import { refreshCart, store } from "../store";

const router = useRouter();
const message = useMessage();

const loading = ref(true);
const submitting = ref(false);
const addresses = ref([]);
const addressId = ref(null);
const preview = ref(null);
const remark = ref("");
const errorText = ref("");
const requestId = ref(
  `checkout-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
);

const addressOptions = computed(() =>
  addresses.value.map((item) => ({
    label: `${item.receiver} · ${item.phone} · ${item.detail}`,
    value: item.id,
  })),
);

const cartItemIds = computed(() => store.checkoutIds || []);

async function loadAddresses() {
  const data = await http.get("/addresses");
  addresses.value = data.items;
  const preferred = data.items.find((item) => item.isDefault) || data.items[0];
  addressId.value = addressId.value || preferred?.id || null;
}

async function loadPreview() {
  if (!cartItemIds.value.length) {
    loading.value = false;
    return;
  }
  if (!addressId.value) {
    loading.value = false;
    return;
  }
  loading.value = true;
  errorText.value = "";
  try {
    preview.value = await http.post("/orders/preview", {
      cartItemIds: cartItemIds.value,
      addressId: addressId.value,
    });
  } catch (error) {
    errorText.value = error.message;
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (!preview.value) return;
  submitting.value = true;
  errorText.value = "";
  try {
    const order = await http.post("/orders", {
      cartItemIds: cartItemIds.value,
      addressId: addressId.value,
      requestId: requestId.value,
      remark: remark.value,
    });
    store.checkoutIds = [];
    await refreshCart();
    message.success(`下单成功，订单号 ${order.orderNo}`);
    router.push("/orders");
  } catch (error) {
    errorText.value = error.message;
    await loadPreview();
  } finally {
    submitting.value = false;
  }
}

async function init() {
  try {
    await loadAddresses();
    await loadPreview();
  } catch (error) {
    errorText.value = error.message;
    loading.value = false;
  }
}

onMounted(init);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">确认订单</h1>
        <p class="page-sub">价格、优惠和库存都按提交那一刻重新计算。</p>
      </div>
      <n-button text type="primary" @click="router.push('/addresses')">管理收货地址</n-button>
    </div>

    <n-empty v-if="!cartItemIds.length" description="没有待结算的商品" class="empty">
      <template #extra>
        <n-button type="primary" @click="router.push('/cart')">回购物车</n-button>
      </template>
    </n-empty>

    <n-spin v-else :show="loading">
      <n-card title="收货地址" class="block">
        <n-select
          v-model:value="addressId"
          :options="addressOptions"
          placeholder="选择收货地址"
          :disabled="!addresses.length"
          @update:value="loadPreview"
        />
        <n-alert v-if="!addresses.length" type="warning" :show-icon="false" style="margin-top: 12px">
          还没有收货地址，先去新增一条再回来结算。
        </n-alert>
      </n-card>

      <n-card v-if="preview" title="商品明细" class="block">
        <div v-for="item in preview.items" :key="item.skuId" class="line">
          <div class="line-main">
            <div class="row-between">
              <span class="name">{{ item.productName }}</span>
              <n-tag v-if="item.activityName" size="small" type="error" :bordered="false">
                {{ item.activityName }}
              </n-tag>
            </div>
            <div class="muted spec">
              {{ Object.values(item.specs || {}).join(" / ") || "默认规格" }} ·
              {{ money(item.unitPrice) }} × {{ item.quantity }}
            </div>
            <div v-if="!item.purchasable" class="warn">{{ item.issue }}</div>
          </div>
          <div class="line-amount">{{ money(item.subtotal) }}</div>
        </div>

        <n-alert
          v-if="preview.issues?.length"
          type="error"
          :show-icon="false"
          style="margin-top: 14px"
        >
          有商品当前不可购买：{{ preview.issues.map((item) => item.reason).join("；") }}
        </n-alert>

        <div class="summary">
          <div><span class="muted">商品原价</span> {{ money(preview.originalAmount) }}</div>
          <div><span class="muted">优惠</span> -{{ money(preview.discountAmount) }}</div>
          <div class="total">
            <span class="muted">应付</span>
            <span class="price big">{{ money(preview.totalAmount) }}</span>
          </div>
        </div>

        <n-input
          v-model:value="remark"
          type="textarea"
          placeholder="备注（可选），例如希望周末自提"
          :maxlength="255"
          show-count
          style="margin-top: 14px"
        />

        <n-alert v-if="errorText" type="error" :show-icon="false" style="margin-top: 14px">
          {{ errorText }}
        </n-alert>

        <div class="actions">
          <n-space>
            <n-button @click="router.push('/cart')">返回购物车</n-button>
            <n-button
              type="primary"
              size="large"
              :loading="submitting"
              :disabled="!!preview.issues?.length"
              @click="submit"
            >
              提交订单 · {{ money(preview.totalAmount) }}
            </n-button>
          </n-space>
        </div>
      </n-card>
    </n-spin>
  </div>
</template>

<style scoped>
.block {
  margin-bottom: 16px;
}

.line {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px dashed var(--line);
}

.name {
  font-weight: 600;
}

.spec {
  margin-top: 4px;
  font-size: 12px;
}

.warn {
  color: #d92d20;
  font-size: 12px;
  margin-top: 4px;
}

.line-amount {
  font-weight: 600;
  white-space: nowrap;
}

.summary {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  font-size: 14px;
}

.total {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.big {
  font-size: 24px;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
