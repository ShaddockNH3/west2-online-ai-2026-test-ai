<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NPagination,
  NSelect,
  NTag,
  useMessage,
} from "naive-ui";
import { http } from "../../api";

const message = useMessage();

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 15;
const status = ref("");
const running = ref(false);

const filters = [
  { label: "全部", value: "" },
  { label: "待执行", value: "PENDING" },
  { label: "执行中", value: "RUNNING" },
  { label: "成功", value: "SUCCEEDED" },
  { label: "失败", value: "FAILED" },
];

const jobLabels = {
  CLOSE_EXPIRED_ORDER: "超时关单",
  BUILD_FULFILLMENT: "生成履约单",
  SEND_ORDER_NOTIFICATION: "订单通知",
  CREATE_FLASH_ORDER: "秒杀建单",
  RELEASE_FLASH_RESERVATION: "释放秒杀占用",
};

async function load() {
  const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
  if (status.value) params.set("status", status.value);
  try {
    const data = await http.get(`/admin/jobs?${params.toString()}`);
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  }
}

async function runOnce() {
  running.value = true;
  try {
    const data = await http.post("/admin/jobs/run-once", {});
    message.success(`执行了 ${data.processed} 条任务`);
    await load();
  } catch (error) {
    message.error(error.message);
  } finally {
    running.value = false;
  }
}

async function retry(row) {
  try {
    await http.post(`/admin/jobs/${row.id}/retry`, { reset_attempts: true });
    message.success("已重新排队");
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString("zh-CN") : "—";
}

const columns = computed(() => [
  { title: "ID", key: "id", width: 60 },
  {
    title: "任务",
    key: "type",
    width: 130,
    render: (row) => jobLabels[row.type] || row.type,
  },
  {
    title: "状态",
    key: "status",
    width: 100,
    render: (row) =>
      h(
        NTag,
        {
          size: "small",
          bordered: false,
          type:
            row.status === "SUCCEEDED"
              ? "success"
              : row.status === "FAILED"
                ? "error"
                : row.status === "RUNNING"
                  ? "warning"
                  : "default",
        },
        () => row.status,
      ),
  },
  {
    title: "尝试",
    key: "attempts",
    width: 90,
    render: (row) => `${row.attempts}/${row.maxAttempts}`,
  },
  { title: "下次执行", key: "nextRunAt", width: 180, render: (row) => formatTime(row.nextRunAt) },
  {
    title: "失败原因",
    key: "lastError",
    render: (row) => row.lastError || "—",
  },
  {
    title: "操作",
    key: "actions",
    width: 100,
    render: (row) =>
      row.status === "FAILED" || row.status === "PENDING"
        ? h(NButton, { size: "tiny", onClick: () => retry(row) }, () => "重新执行")
        : null,
  },
]);

onMounted(load);
</script>

<template>
  <div class="panel">
    <n-card size="small" title="后台任务">
      <template #header-extra>
        <n-button size="small" type="primary" :loading="running" @click="runOnce">
          立即执行待办
        </n-button>
      </template>

      <div class="filters">
        <n-select
          v-model:value="status"
          :options="filters"
          size="small"
          style="width: 160px"
          @update:value="page = 1; load()"
        />
      </div>

      <n-data-table :columns="columns" :data="rows" :bordered="false" :single-line="false" size="small" />
      <div class="pager">
        <n-pagination v-model:page="page" :page-size="pageSize" :item-count="total" @update:page="load" />
      </div>
      <p class="hint">
        任务存在数据库里，应用重启后仍在；连续失败会停在这一页，点「重新执行」可以再排队一次。
      </p>
    </n-card>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 12px;
}

.filters {
  margin-bottom: 12px;
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
</style>
