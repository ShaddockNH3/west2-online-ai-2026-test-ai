<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NSpace,
  NTag,
  useMessage,
} from "naive-ui";
import { http } from "../../api";

const message = useMessage();

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 12;
const keyword = ref("");
const lowStock = ref(false);

const modalVisible = ref(false);
const modalMode = ref("inbound");
const target = ref(null);
const amount = ref(1);
const saving = ref(false);

const logVisible = ref(false);
const logs = ref([]);
const logSku = ref(null);

async function load() {
  const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
  if (keyword.value.trim()) params.set("keyword", keyword.value.trim());
  if (lowStock.value) params.set("lowStock", "5");
  try {
    const data = await http.get(`/admin/inventory?${params.toString()}`);
    rows.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  }
}

function openInbound(row) {
  target.value = row;
  modalMode.value = "inbound";
  amount.value = 1;
  modalVisible.value = true;
}

function openAdjust(row) {
  target.value = row;
  modalMode.value = "adjust";
  amount.value = row.available;
  modalVisible.value = true;
}

async function save() {
  saving.value = true;
  try {
    if (modalMode.value === "inbound") {
      await http.post(`/admin/skus/${target.value.skuId}/inventory`, {
        quantity: amount.value,
        reason: "管理员入库",
      });
      message.success("已入库");
    } else {
      await http.put(`/admin/skus/${target.value.skuId}/inventory`, {
        available: amount.value,
        reason: "管理员盘点调整",
      });
      message.success("库存已调整");
    }
    modalVisible.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  } finally {
    saving.value = false;
  }
}

async function openLogs(row) {
  logSku.value = row;
  const data = await http.get(`/admin/inventory/logs?skuId=${row.skuId}&pageSize=30`);
  logs.value = data.items;
  logVisible.value = true;
}

const columns = computed(() => [
  { title: "商品", key: "productName" },
  { title: "SKU", key: "skuCode", width: 130 },
  {
    title: "规格",
    key: "specs",
    width: 160,
    render: (row) => Object.values(row.specs || {}).join(" / ") || "默认",
  },
  {
    title: "可售",
    key: "available",
    width: 80,
    render: (row) =>
      h(
        NTag,
        { size: "small", type: row.available <= 5 ? "error" : "success", bordered: false },
        () => row.available,
      ),
  },
  { title: "占用", key: "reserved", width: 70 },
  { title: "已售", key: "sold", width: 70 },
  {
    title: "操作",
    key: "actions",
    width: 190,
    render: (row) =>
      h(NSpace, { size: 4 }, () => [
        h(NButton, { size: "tiny", onClick: () => openInbound(row) }, () => "入库"),
        h(NButton, { size: "tiny", onClick: () => openAdjust(row) }, () => "盘点"),
        h(NButton, { size: "tiny", text: true, onClick: () => openLogs(row) }, () => "流水"),
      ]),
  },
]);

onMounted(load);
</script>

<template>
  <div class="panel">
    <n-card size="small" title="库存">
      <div class="filters">
        <n-input
          v-model:value="keyword"
          placeholder="搜商品名或 SKU 编码"
          size="small"
          style="width: 220px"
          @keyup.enter="load"
        />
        <n-button size="small" @click="load">搜索</n-button>
        <n-button
          size="small"
          :type="lowStock ? 'primary' : 'default'"
          :secondary="lowStock"
          @click="lowStock = !lowStock; load()"
        >
          只看低库存
        </n-button>
      </div>

      <n-data-table :columns="columns" :data="rows" :bordered="false" :single-line="false" size="small" />
      <div class="pager">
        <n-pagination v-model:page="page" :page-size="pageSize" :item-count="total" @update:page="load" />
      </div>
    </n-card>

    <n-modal v-model:show="modalVisible" preset="card" :title="modalMode === 'inbound' ? '入库' : '盘点调整'" style="width: 420px">
      <p class="muted small">{{ target?.productName }} · {{ target?.skuCode }}</p>
      <div class="field">
        <div class="label">{{ modalMode === "inbound" ? "入库数量" : "调整后可用库存" }}</div>
        <n-input-number v-model:value="amount" :min="modalMode === 'inbound' ? 1 : 0" style="width: 180px" />
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="save">确认</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-drawer v-model:show="logVisible" :width="520">
      <n-drawer-content :title="`库存流水 · ${logSku?.skuCode || ''}`" closable>
        <div v-for="log in logs" :key="log.id" class="log-row">
          <div>
            <n-tag size="small" :bordered="false">{{ log.changeType }}</n-tag>
            <span class="log-reason">{{ log.reason }}</span>
          </div>
          <div class="log-right">
            <div :class="log.quantity >= 0 ? 'plus' : 'minus'">
              {{ log.quantity > 0 ? "+" : "" }}{{ log.quantity }}
            </div>
            <div class="muted small">{{ log.availableBefore }} → {{ log.availableAfter }}</div>
            <div v-if="log.orderNo" class="muted small">{{ log.orderNo }}</div>
          </div>
        </div>
        <p v-if="!logs.length" class="muted">还没有库存变化记录</p>
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
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.field {
  margin-top: 14px;
}

.label {
  font-size: 12px;
  color: #334155;
  margin-bottom: 6px;
}

.small {
  font-size: 12px;
}

.log-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--line);
}

.log-reason {
  margin-left: 8px;
  font-size: 13px;
}

.log-right {
  text-align: right;
  font-size: 13px;
}

.plus {
  color: #0f9d58;
  font-weight: 600;
}

.minus {
  color: #d92d20;
  font-weight: 600;
}
</style>
