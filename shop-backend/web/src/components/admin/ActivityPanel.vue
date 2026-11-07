<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NDatePicker,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  NSpace,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../../api";

const message = useMessage();

const activities = ref([]);
const visible = ref(false);
const saving = ref(false);
const form = ref({
  name: "",
  type: "FIXED_PRICE",
  status: "ACTIVE",
  startsAt: Date.now() - 3600 * 1000,
  endsAt: Date.now() + 7 * 24 * 3600 * 1000,
  description: "",
  skus: [{ skuId: null, activityPrice: "", saleQuota: null, perUserLimit: null }],
});

const typeOptions = [
  { label: "固定活动价", value: "FIXED_PRICE" },
  { label: "限量发售", value: "FLASH_SALE" },
];
const statusOptions = [
  { label: "进行中（ACTIVE）", value: "ACTIVE" },
  { label: "草稿（DRAFT）", value: "DRAFT" },
  { label: "停用（DISABLED）", value: "DISABLED" },
];

async function load() {
  try {
    const data = await http.get("/admin/activities");
    activities.value = data.items;
  } catch (error) {
    message.error(error.message);
  }
}

function openCreate() {
  form.value = {
    name: "",
    type: "FIXED_PRICE",
    status: "ACTIVE",
    startsAt: Date.now() - 3600 * 1000,
    endsAt: Date.now() + 7 * 24 * 3600 * 1000,
    description: "",
    skus: [{ skuId: null, activityPrice: "", saleQuota: null, perUserLimit: null }],
  };
  visible.value = true;
}

function addSkuRow() {
  form.value.skus.push({ skuId: null, activityPrice: "", saleQuota: null, perUserLimit: null });
}

function removeSkuRow(index) {
  form.value.skus.splice(index, 1);
}

async function save() {
  if (!form.value.name) {
    message.warning("活动名要填");
    return;
  }
  const skus = form.value.skus
    .filter((item) => item.skuId && item.activityPrice)
    .map((item) => ({
      skuId: item.skuId,
      activityPrice: item.activityPrice,
      saleQuota: item.saleQuota || null,
      perUserLimit: item.perUserLimit || null,
    }));
  if (!skus.length) {
    message.warning("至少配置一个参加活动的 SKU");
    return;
  }
  saving.value = true;
  try {
    await http.post("/admin/activities", {
      name: form.value.name,
      type: form.value.type,
      status: form.value.status,
      description: form.value.description,
      startsAt: new Date(form.value.startsAt).toISOString(),
      endsAt: new Date(form.value.endsAt).toISOString(),
      skus,
    });
    message.success("活动已创建");
    visible.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  } finally {
    saving.value = false;
  }
}

async function toggle(activity) {
  try {
    await http.patch(`/admin/activities/${activity.id}`, {
      status: activity.status === "ACTIVE" ? "DISABLED" : "ACTIVE",
    });
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

const columns = computed(() => [
  { title: "ID", key: "id", width: 56 },
  { title: "活动名", key: "name" },
  {
    title: "类型",
    key: "type",
    width: 110,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.type === "FLASH_SALE" ? "error" : "info" },
        () => (row.type === "FLASH_SALE" ? "限量发售" : "固定价")),
  },
  {
    title: "状态",
    key: "status",
    width: 120,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.running ? "success" : "default" },
        () => (row.running ? "进行中" : row.status)),
  },
  { title: "时间窗", key: "window", width: 210, render: (row) => `${row.startsAt?.slice(5, 16)} → ${row.endsAt?.slice(5, 16)}` },
  {
    title: "SKU",
    key: "skus",
    render: (row) =>
      h(NSpace, { size: 4 }, () =>
        row.skus.map((sku) =>
          h(NTag, { size: "small", bordered: false }, () =>
            `${sku.skuCode} ${money(sku.activityPrice)}${sku.saleQuota ? ` (${sku.soldCount}/${sku.saleQuota})` : ""}`,
          ),
        ),
      ),
  },
  {
    title: "操作",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, { size: "tiny", onClick: () => toggle(row) }, () => (row.status === "ACTIVE" ? "停用" : "启用")),
  },
]);

onMounted(load);
</script>

<template>
  <div class="panel">
    <n-card size="small" title="活动列表">
      <template #header-extra>
        <n-button size="small" type="primary" @click="openCreate">新建活动</n-button>
      </template>
      <n-data-table :columns="columns" :data="activities" :bordered="false" :single-line="false" size="small" />
      <p class="hint">
        固定价活动会参与前台选价；限量发售活动走「限量抢购」页，按活动价、配额和限购规则售卖。
      </p>
    </n-card>

    <n-modal v-model:show="visible" preset="card" title="新建活动" style="width: 620px">
      <n-form label-placement="top">
        <n-form-item label="活动名">
          <n-input v-model:value="form.name" placeholder="例如：开学季周边特惠" />
        </n-form-item>
        <n-space>
          <n-form-item label="类型">
            <n-select v-model:value="form.type" :options="typeOptions" style="width: 180px" />
          </n-form-item>
          <n-form-item label="状态">
            <n-select v-model:value="form.status" :options="statusOptions" style="width: 200px" />
          </n-form-item>
        </n-space>
        <n-space>
          <n-form-item label="开始时间">
            <n-date-picker v-model:value="form.startsAt" type="datetime" style="width: 220px" />
          </n-form-item>
          <n-form-item label="结束时间">
            <n-date-picker v-model:value="form.endsAt" type="datetime" style="width: 220px" />
          </n-form-item>
        </n-space>
        <n-form-item label="说明">
          <n-input v-model:value="form.description" placeholder="可选" />
        </n-form-item>
      </n-form>

      <div class="sku-head">
        <span>参加活动的 SKU</span>
        <n-button size="tiny" @click="addSkuRow">加一行</n-button>
      </div>
      <div v-for="(row, index) in form.skus" :key="index" class="sku-form-row">
        <n-input-number v-model:value="row.skuId" placeholder="SKU ID" :min="1" style="width: 110px" />
        <n-input v-model:value="row.activityPrice" placeholder="活动价 9.00" style="width: 120px" />
        <n-input-number v-model:value="row.saleQuota" placeholder="发售数量" :min="1" style="width: 120px" />
        <n-input-number v-model:value="row.perUserLimit" placeholder="每人限购" :min="1" style="width: 110px" />
        <n-button size="tiny" text type="error" @click="removeSkuRow(index)">删除</n-button>
      </div>
      <p class="hint">限量发售要填发售数量，固定价活动可以留空。</p>

      <template #footer>
        <n-space justify="end">
          <n-button @click="visible = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="save">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 12px;
}

.hint {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.sku-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 6px 0 8px;
  font-size: 13px;
  font-weight: 600;
}

.sku-form-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
</style>
