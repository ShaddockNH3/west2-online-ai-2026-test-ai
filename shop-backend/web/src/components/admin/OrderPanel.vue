<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NInput,
  NSelect,
  NPagination,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../../api";
import { statusText, statusType } from "../../theme";

const message = useMessage();

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 12;
const status = ref("");
const keyword = ref("");
const loading = ref(false);

const visible = ref(false);
const detail = ref(null);
const detailLoading = ref(false);

const filters = [
  { label: "全部", value: "" },
  { label: "待支付", value: "PENDING_PAYMENT" },
  { label: "已支付", value: "PAID" },
  { label: "已发货", value: "SHIPPED" },
  { label: "已完成", value: "COMPLETED" },
  { label: "已取消", value: "CANCELLED" },
];

async function load() {
  loading.value = true;
  const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
  if (status.value) params.set("status", status.value);
  if (keyword.value.trim()) params.set("keyword", keyword.value.trim());
  try {
    const data = await http.get(`/admin/orders?${params.toString()}`);
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function openDetail(row) {
  visible.value = true;
  detailLoading.value = true;
  try {
    detail.value = await http.get(`/admin/orders/${row.orderNo}`);
  } catch (error) {
    message.error(error.message);
    visible.value = false;
  } finally {
    detailLoading.value = false;
  }
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "—";
}

const columns = computed(() => [
  { title: "订单号", key: "orderNo", width: 200 },
  { title: "下单用户", key: "username", width: 110 },
  {
    title: "状态",
    key: "status",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", type: statusType[row.status] || "default", bordered: false },
        () => statusText[row.status] || row.status),
  },
  { title: "金额", key: "totalAmount", width: 100, render: (row) => money(row.totalAmount) },
  { title: "件数", key: "itemCount", width: 70 },
  { title: "下单时间", key: "createdAt", width: 180, render: (row) => formatTime(row.createdAt) },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render: (row) => h(NButton, { size: "tiny", onClick: () => openDetail(row) }, () => "详情"),
  },
]);

onMounted(load);
</script>

<template>
  <div class="panel">
    <n-card size="small" title="全部订单">
      <div class="filters">
        <n-select
          v-model:value="status"
          :options="filters"
          size="small"
          style="width: 160px"
          @update:value="page = 1; load()"
        />
        <n-input
          v-model:value="keyword"
          placeholder="按订单号查"
          size="small"
          style="width: 200px"
          @keyup.enter="page = 1; load()"
        />
      </div>

      <n-spin :show="loading">
        <n-data-table :columns="columns" :data="rows" :bordered="false" :single-line="false" size="small" />
      </n-spin>
      <div class="pager">
        <n-pagination v-model:page="page" :page-size="pageSize" :item-count="total" @update:page="load" />
      </div>
    </n-card>

    <n-drawer v-model:show="visible" :width="520">
      <n-drawer-content title="订单详情" closable>
        <n-spin :show="detailLoading">
          <div v-if="detail">
            <div class="row-between">
              <n-tag :type="statusType[detail.status]" :bordered="false">
                {{ statusText[detail.status] }}
              </n-tag>
              <span class="muted small">{{ detail.orderNo }}</span>
            </div>
            <div class="meta">
              <div>下单：{{ formatTime(detail.createdAt) }}</div>
              <div v-if="detail.paidAt">支付：{{ formatTime(detail.paidAt) }}</div>
              <div v-if="detail.shippedAt">发货：{{ formatTime(detail.shippedAt) }}</div>
              <div v-if="detail.cancelledAt">取消：{{ formatTime(detail.cancelledAt) }}</div>
            </div>
            <div class="section">
              <div class="section-title">收货信息</div>
              <div>{{ detail.receiver }} · {{ detail.phone }}</div>
              <div class="muted">{{ detail.addressDetail }}</div>
            </div>
            <div class="section">
              <div class="section-title">商品</div>
              <div v-for="(item, index) in detail.items" :key="index" class="item">
                <div>
                  <div>{{ item.productName }}</div>
                  <div class="muted small">
                    {{ Object.values(item.specs || {}).join(" / ") }} · {{ money(item.unitPrice) }} × {{ item.quantity }}
                  </div>
                </div>
                <div>{{ money(item.subtotal) }}</div>
              </div>
            </div>
            <div class="section amounts">
              <div>原价 {{ money(detail.originalAmount) }}</div>
              <div>优惠 -{{ money(detail.discountAmount) }}</div>
              <div class="total">应付 <span class="price">{{ money(detail.totalAmount) }}</span></div>
            </div>
            <div v-if="detail.fulfillment" class="section">
              <div class="section-title">履约</div>
              <div>{{ detail.fulfillment.status }} · {{ detail.fulfillment.trackingNo || "未发货" }}</div>
            </div>
          </div>
        </n-spin>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 12px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.meta {
  margin-top: 12px;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section {
  margin-top: 16px;
  padding-top: 12px;
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

.amounts {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
  font-size: 13px;
}

.total {
  font-size: 17px;
}

.small {
  font-size: 12px;
}
</style>
