<script setup>
import { computed, h, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NButton,
  NCard,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NModal,
  NRadio,
  NRadioGroup,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../api";
import { fulfillmentText, statusText, statusType } from "../theme";

const router = useRouter();
const message = useMessage();

const loading = ref(false);
const orders = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const status = ref("");

const detailVisible = ref(false);
const detail = ref(null);
const detailLoading = ref(false);

const payVisible = ref(false);
const payTarget = ref(null);
const payResult = ref("SUCCESS");
const paying = ref(false);

const statusFilters = [
  { label: "全部订单", value: "" },
  { label: "待支付", value: "PENDING_PAYMENT" },
  { label: "已支付", value: "PAID" },
  { label: "已发货", value: "SHIPPED" },
  { label: "已完成", value: "COMPLETED" },
  { label: "已取消", value: "CANCELLED" },
];

function formatTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN");
}

async function load() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
    if (status.value) params.set("status", status.value);
    const data = await http.get(`/orders?${params.toString()}`);
    orders.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

function filter(value) {
  status.value = value;
  page.value = 1;
  load();
}

async function openDetail(row) {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    detail.value = await http.get(`/orders/${row.orderNo}`);
  } catch (error) {
    message.error(error.message);
    detailVisible.value = false;
  } finally {
    detailLoading.value = false;
  }
}

function openPay(row) {
  payTarget.value = row;
  payResult.value = "SUCCESS";
  payVisible.value = true;
}

async function submitPay() {
  paying.value = true;
  try {
    const payment = await http.post(`/orders/${payTarget.value.orderNo}/payments`, {
      result: payResult.value,
    });
    if (payment.status === "SUCCESS") {
      message.success("模拟支付成功");
      payVisible.value = false;
    } else {
      message.warning("模拟支付失败，订单仍待支付，可以再试一次");
    }
    await load();
    if (detail.value?.orderNo === payTarget.value.orderNo) await refreshDetail();
  } catch (error) {
    message.error(error.message);
  } finally {
    paying.value = false;
  }
}

async function cancelOrder(row) {
  try {
    await http.post(`/orders/${row.orderNo}/cancel`, {});
    message.success("订单已取消");
    await load();
    if (detail.value?.orderNo === row.orderNo) await refreshDetail();
  } catch (error) {
    message.error(error.message);
  }
}

async function confirmOrder(row) {
  try {
    await http.post(`/orders/${row.orderNo}/confirm`, {});
    message.success("已确认收货");
    await load();
    if (detail.value?.orderNo === row.orderNo) await refreshDetail();
  } catch (error) {
    message.error(error.message);
  }
}

async function refreshDetail() {
  if (!detail.value) return;
  detail.value = await http.get(`/orders/${detail.value.orderNo}`);
}

const columns = computed(() => [
  { title: "订单号", key: "orderNo", width: 210 },
  {
    title: "状态",
    key: "status",
    width: 110,
    render: (row) =>
      h(NTag, { type: statusType[row.status] || "default", bordered: false }, () => statusText[row.status] || row.status),
  },
  { title: "金额", key: "totalAmount", width: 110, render: (row) => money(row.totalAmount) },
  { title: "商品数", key: "itemCount", width: 90 },
  { title: "下单时间", key: "createdAt", width: 190, render: (row) => formatTime(row.createdAt) },
  {
    title: "操作",
    key: "actions",
    render: (row) =>
      h(NSpace, { size: 6 }, () => [
        h(NButton, { size: "small", quaternary: true, onClick: () => openDetail(row) }, () => "详情"),
        row.status === "PENDING_PAYMENT"
          ? h(NButton, { size: "small", type: "primary", onClick: () => openPay(row) }, () => "支付")
          : null,
        row.status === "PENDING_PAYMENT"
          ? h(NButton, { size: "small", quaternary: true, onClick: () => cancelOrder(row) }, () => "取消")
          : null,
        row.status === "SHIPPED"
          ? h(NButton, { size: "small", type: "primary", onClick: () => confirmOrder(row) }, () => "确认收货")
          : null,
      ]),
  },
]);

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">我的订单</h1>
        <p class="page-sub">下单后在这里支付、取消和确认收货。历史订单的商品信息是快照，不会随改价变化。</p>
      </div>
      <n-button @click="router.push('/')">继续购物</n-button>
    </div>

    <n-card>
      <n-select
        :value="status"
        :options="statusFilters"
        size="small"
        style="width: 160px; margin-bottom: 14px"
        @update:value="filter"
      />

      <n-spin :show="loading">
        <n-data-table
          v-if="orders.length"
          :columns="columns"
          :data="orders"
          :bordered="false"
          :single-line="false"
        />
        <n-empty v-else description="还没有订单" class="empty">
          <template #extra>
            <n-button type="primary" @click="router.push('/')">去挑点周边</n-button>
          </template>
        </n-empty>
      </n-spin>
    </n-card>

    <n-drawer v-model:show="detailVisible" :width="520">
      <n-drawer-content title="订单详情" closable>
        <n-spin :show="detailLoading">
          <div v-if="detail" class="detail">
            <div class="row-between">
              <n-tag :type="statusType[detail.status]" :bordered="false">
                {{ statusText[detail.status] }}
              </n-tag>
              <span class="muted mono">{{ detail.orderNo }}</span>
            </div>

            <div class="meta">
              <div><span class="muted">下单</span> {{ formatTime(detail.createdAt) }}</div>
              <div v-if="detail.paidAt"><span class="muted">支付</span> {{ formatTime(detail.paidAt) }}</div>
              <div v-if="detail.shippedAt"><span class="muted">发货</span> {{ formatTime(detail.shippedAt) }}</div>
              <div v-if="detail.cancelledAt">
                <span class="muted">取消</span> {{ formatTime(detail.cancelledAt) }}
                （{{ detail.cancelReason === "EXPIRED" ? "超时未支付" : "用户取消" }}）
              </div>
            </div>

            <div class="section">
              <div class="section-title">收货信息</div>
              <div>{{ detail.receiver }} · {{ detail.phone }}</div>
              <div class="muted">{{ detail.addressDetail }}</div>
            </div>

            <div class="section">
              <div class="section-title">商品明细</div>
              <div v-for="(item, index) in detail.items" :key="index" class="item">
                <div>
                  <div class="item-name">{{ item.productName }}</div>
                  <div class="muted small">
                    {{ Object.values(item.specs || {}).join(" / ") || "默认规格" }} ·
                    {{ money(item.unitPrice) }} × {{ item.quantity }}
                  </div>
                  <div v-if="item.activityName" class="small activity">{{ item.activityName }}</div>
                </div>
                <div class="item-amount">{{ money(item.subtotal) }}</div>
              </div>
            </div>

            <div class="section amounts">
              <div><span class="muted">原价</span> {{ money(detail.originalAmount) }}</div>
              <div><span class="muted">优惠</span> -{{ money(detail.discountAmount) }}</div>
              <div class="total"><span class="muted">应付</span> <span class="price">{{ money(detail.totalAmount) }}</span></div>
            </div>

            <div v-if="detail.fulfillment" class="section">
              <div class="section-title">履约进度</div>
              <div class="row-between">
                <n-tag size="small" :bordered="false">{{ fulfillmentText[detail.fulfillment.status] }}</n-tag>
                <span v-if="detail.fulfillment.trackingNo" class="muted small">
                  运单 {{ detail.fulfillment.trackingNo }}
                </span>
              </div>
              <div v-if="detail.fulfillment.lastError" class="small warn">
                {{ detail.fulfillment.lastError }}
              </div>
            </div>

            <div v-if="detail.payments?.length" class="section">
              <div class="section-title">支付记录</div>
              <div v-for="payment in detail.payments" :key="payment.paymentNo" class="payment-line">
                <n-tag size="small" :type="payment.status === 'SUCCESS' ? 'success' : 'error'" :bordered="false">
                  {{ payment.status === "SUCCESS" ? "成功" : "失败" }}
                </n-tag>
                <span>{{ money(payment.amount) }}</span>
                <span class="muted small">{{ formatTime(payment.createdAt) }}</span>
              </div>
            </div>

            <n-space style="margin-top: 18px">
              <n-button
                v-if="detail.status === 'PENDING_PAYMENT'"
                type="primary"
                @click="openPay(detail)"
              >
                去支付
              </n-button>
              <n-button
                v-if="detail.status === 'PENDING_PAYMENT'"
                @click="cancelOrder(detail)"
              >
                取消订单
              </n-button>
              <n-button v-if="detail.status === 'SHIPPED'" type="primary" @click="confirmOrder(detail)">
                确认收货
              </n-button>
            </n-space>
          </div>
          <n-empty v-else description="加载中" />
        </n-spin>
      </n-drawer-content>
    </n-drawer>

    <n-modal
      v-model:show="payVisible"
      preset="card"
      title="模拟支付"
      style="width: 420px"
    >
      <p class="muted small" style="margin-top: 0">
        本地模拟接口，金额由服务端从订单读取，选择这次模拟的结果即可。
      </p>
      <n-radio-group v-model:value="payResult">
        <n-space vertical>
          <n-radio value="SUCCESS">模拟支付成功</n-radio>
          <n-radio value="FAILURE">模拟支付失败</n-radio>
        </n-space>
      </n-radio-group>
      <template #footer>
        <n-space justify="end">
          <n-button @click="payVisible = false">算了</n-button>
          <n-button type="primary" :loading="paying" @click="submitPay">确认</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 12px;
  font-size: 13px;
}

.section {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

.section-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 13px;
}

.item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--line);
}

.item-name {
  font-weight: 500;
}

.small {
  font-size: 12px;
}

.activity {
  color: #d92d20;
  margin-top: 2px;
}

.item-amount {
  font-weight: 600;
}

.amounts {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.total {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 18px;
}

.payment-line {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

.warn {
  color: #d92d20;
  margin-top: 6px;
}
</style>
