<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NSelect,
  NPagination,
  NSpace,
  NSwitch,
  NTag,
  useMessage,
} from "naive-ui";
import { http } from "../../api";
import { fulfillmentText } from "../../theme";

const message = useMessage();

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 12;
const status = ref("");
const simulateFail = ref(false);

const filters = [
  { label: "全部", value: "" },
  { label: "待备货", value: "PENDING" },
  { label: "待发货", value: "READY_TO_SHIP" },
  { label: "已发货", value: "SHIPPED" },
  { label: "已完成", value: "COMPLETED" },
];

async function load() {
  const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
  if (status.value) params.set("status", status.value);
  try {
    const data = await http.get(`/admin/fulfillments?${params.toString()}`);
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  }
}

async function prepare(row) {
  try {
    await http.post(`/admin/fulfillments/${row.fulfillmentNo}/prepare`, {});
    message.success("备货完成");
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function ship(row) {
  try {
    await http.post(`/admin/fulfillments/${row.fulfillmentNo}/ship`, {
      simulate: simulateFail.value ? "FAIL" : "SUCCESS",
    });
    message.success("已发货");
    await load();
  } catch (error) {
    message.error(error.message);
    await load();
  }
}

const columns = computed(() => [
  { title: "履约单", key: "fulfillmentNo", width: 180 },
  { title: "订单", key: "orderNo", width: 200 },
  {
    title: "状态",
    key: "status",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.status === "COMPLETED" ? "success" : "info" },
        () => fulfillmentText[row.status] || row.status),
  },
  { title: "收货人", key: "receiver", width: 100 },
  {
    title: "商品",
    key: "items",
    render: (row) =>
      (row.items || []).map((item) => `${item.productName}×${item.quantity}`).join("，"),
  },
  {
    title: "尝试",
    key: "attempts",
    width: 70,
    render: (row) => (row.attempts ? `${row.attempts} 次` : "—"),
  },
  {
    title: "操作",
    key: "actions",
    width: 180,
    render: (row) =>
      h(NSpace, { size: 6 }, () => [
        row.status === "PENDING"
          ? h(NButton, { size: "tiny", onClick: () => prepare(row) }, () => "备货")
          : null,
        row.status === "READY_TO_SHIP"
          ? h(NButton, { size: "tiny", type: "primary", onClick: () => ship(row) }, () => "发货")
          : null,
        row.lastError
          ? h(NTag, { size: "small", type: "error", bordered: false }, () => "上次失败")
          : null,
      ]),
  },
]);

onMounted(load);
</script>

<template>
  <div class="panel">
    <n-card size="small" title="履约单">
      <div class="filters">
        <n-select
          v-model:value="status"
          :options="filters"
          size="small"
          style="width: 160px"
          @update:value="page = 1; load()"
        />
        <div class="fail-toggle">
          <n-switch v-model:value="simulateFail" size="small" />
          <span class="muted small">发货时模拟物流失败（可再点一次重试）</span>
        </div>
      </div>

      <n-data-table :columns="columns" :data="rows" :bordered="false" :single-line="false" size="small" />
      <div class="pager">
        <n-pagination v-model:page="page" :page-size="pageSize" :item-count="total" @update:page="load" />
      </div>
      <p class="hint">
        支付成功后由后台任务生成履约单；备货完成才能发货，失败会记录尝试次数与原因。
      </p>
    </n-card>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 12px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.fail-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.hint {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.small {
  font-size: 12px;
}
</style>
