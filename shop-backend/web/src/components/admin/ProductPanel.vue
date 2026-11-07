<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPagination,
  NSelect,
  NSpace,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../../api";

const message = useMessage();

const categories = ref([]);
const products = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 10;

const productVisible = ref(false);
const productForm = ref({ name: "", description: "", categoryId: null });
const savingProduct = ref(false);

const skuVisible = ref(false);
const currentProduct = ref(null);
const skus = ref([]);
const skuForm = ref({ specsText: "", price: "", stock: 0 });
const savingSku = ref(false);

const categoryName = ref("");
const categoryOptions = computed(() =>
  categories.value.map((item) => ({ label: item.name, value: item.id })),
);

async function loadCategories() {
  const data = await http.get("/admin/categories");
  categories.value = data.items;
}

async function loadProducts() {
  const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
  const data = await http.get(`/admin/products?${params.toString()}`);
  products.value = data.items;
  total.value = data.total;
}

async function createCategory() {
  if (!categoryName.value.trim()) return;
  try {
    await http.post("/admin/categories", { name: categoryName.value.trim() });
    categoryName.value = "";
    await loadCategories();
    message.success("类目已添加");
  } catch (error) {
    message.error(error.message);
  }
}

async function toggleCategory(category) {
  try {
    await http.patch(`/admin/categories/${category.id}`, {
      status: category.status === "ENABLED" ? "DISABLED" : "ENABLED",
    });
    await loadCategories();
  } catch (error) {
    message.error(error.message);
  }
}

function openProductModal() {
  productForm.value = { name: "", description: "", categoryId: categoryOptions.value[0]?.value || null };
  productVisible.value = true;
}

async function createProduct() {
  if (!productForm.value.name || !productForm.value.categoryId) {
    message.warning("名称和类目都要填");
    return;
  }
  savingProduct.value = true;
  try {
    await http.post("/admin/products", productForm.value);
    productVisible.value = false;
    await loadProducts();
    message.success("商品已创建，记得加 SKU 再上架");
  } catch (error) {
    message.error(error.message);
  } finally {
    savingProduct.value = false;
  }
}

async function toggleStatus(row) {
  try {
    await http.patch(`/admin/products/${row.id}/status`, {
      status: row.status === "ON_SALE" ? "OFF_SALE" : "ON_SALE",
    });
    await loadProducts();
  } catch (error) {
    message.error(error.message);
  }
}

async function openSkus(row) {
  currentProduct.value = row;
  skuForm.value = { specsText: "", price: "", stock: 0 };
  skuVisible.value = true;
  await loadSkus();
}

async function loadSkus() {
  if (!currentProduct.value) return;
  const data = await http.get(`/admin/products/${currentProduct.value.id}/skus`);
  skus.value = data.items;
}

function parseSpecs(text) {
  const result = {};
  for (const part of text.split(/[,，]/)) {
    const [key, value] = part.split(/[=:：]/);
    if (key?.trim() && value?.trim()) result[key.trim()] = value.trim();
  }
  return result;
}

async function createSku() {
  const specs = parseSpecs(skuForm.value.specsText);
  if (!skuForm.value.price) {
    message.warning("价格要填");
    return;
  }
  savingSku.value = true;
  try {
    await http.post(`/admin/products/${currentProduct.value.id}/skus`, {
      specs,
      price: skuForm.value.price,
      stock: skuForm.value.stock || 0,
    });
    skuForm.value = { specsText: "", price: "", stock: 0 };
    await loadSkus();
    message.success("SKU 已添加");
  } catch (error) {
    message.error(error.message);
  } finally {
    savingSku.value = false;
  }
}

const columns = computed(() => [
  { title: "ID", key: "id", width: 64 },
  { title: "商品名", key: "name" },
  { title: "类目", key: "categoryName", width: 110 },
  {
    title: "状态",
    key: "status",
    width: 100,
    render: (row) =>
      h(
        NTag,
        {
          size: "small",
          type: row.status === "ON_SALE" ? "success" : "default",
          bordered: false,
        },
        () => (row.status === "ON_SALE" ? "在售" : "下架"),
      ),
  },
  {
    title: "操作",
    key: "actions",
    width: 220,
    render: (row) =>
      h(NSpace, { size: 6 }, () => [
        h(NButton, { size: "tiny", onClick: () => openSkus(row) }, () => "SKU / 库存"),
        h(
          NButton,
          { size: "tiny", type: row.status === "ON_SALE" ? "default" : "primary", onClick: () => toggleStatus(row) },
          () => (row.status === "ON_SALE" ? "下架" : "上架"),
        ),
      ]),
  },
]);

onMounted(async () => {
  await loadCategories();
  await loadProducts();
});
</script>

<template>
  <div class="panel">
    <n-card size="small" title="类目" class="block">
      <div class="cat-row">
        <n-tag
          v-for="item in categories"
          :key="item.id"
          :type="item.status === 'ENABLED' ? 'success' : 'default'"
          :bordered="false"
          closable
          @close="toggleCategory(item)"
        >
          {{ item.name }}{{ item.status === "ENABLED" ? "" : "（已停用）" }}
        </n-tag>
        <n-input
          v-model:value="categoryName"
          placeholder="新类目名"
          size="small"
          style="width: 160px"
          @keyup.enter="createCategory"
        />
        <n-button size="small" type="primary" secondary @click="createCategory">添加</n-button>
      </div>
      <p class="hint">点标签上的 × 可以停用类目；停用后该类目下的商品不出现在前台。</p>
    </n-card>

    <n-card size="small" title="商品" class="block">
      <template #header-extra>
        <n-button size="small" type="primary" @click="openProductModal">新增商品</n-button>
      </template>
      <n-data-table
        :columns="columns"
        :data="products"
        :bordered="false"
        :single-line="false"
        size="small"
      />
      <div class="pager">
        <n-pagination
          v-model:page="page"
          :page-size="pageSize"
          :item-count="total"
          @update:page="loadProducts"
        />
      </div>
    </n-card>

    <n-modal v-model:show="productVisible" preset="card" title="新增商品" style="width: 480px">
      <n-form label-placement="top">
        <n-form-item label="商品名称">
          <n-input v-model:value="productForm.name" placeholder="例如：工作室卫衣" />
        </n-form-item>
        <n-form-item label="所属类目">
          <n-select v-model:value="productForm.categoryId" :options="categoryOptions" />
        </n-form-item>
        <n-form-item label="商品介绍">
          <n-input
            v-model:value="productForm.description"
            type="textarea"
            placeholder="材质、尺码建议等"
            :maxlength="2000"
            show-count
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="productVisible = false">取消</n-button>
          <n-button type="primary" :loading="savingProduct" @click="createProduct">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-drawer v-model:show="skuVisible" :width="560">
      <n-drawer-content :title="`SKU · ${currentProduct?.name || ''}`" closable>
        <n-card size="small" title="新增 SKU" class="block">
          <n-form label-placement="top">
            <n-form-item label="规格（格式：颜色=黑色,尺码=M）">
              <n-input v-model:value="skuForm.specsText" placeholder="没有多规格可以留空" />
            </n-form-item>
            <n-form-item label="价格（元）">
              <n-input v-model:value="skuForm.price" placeholder="例如 59.00" />
            </n-form-item>
            <n-form-item label="初始库存">
              <n-input-number v-model:value="skuForm.stock" :min="0" style="width: 160px" />
            </n-form-item>
            <n-button type="primary" :loading="savingSku" @click="createSku">添加 SKU</n-button>
          </n-form>
        </n-card>

        <div v-for="sku in skus" :key="sku.id" class="sku-row">
          <div>
            <div class="sku-code">{{ sku.code }}</div>
            <div class="muted small">
              {{ Object.entries(sku.specs || {}).map(([key, value]) => `${key}=${value}`).join("，") || "默认规格" }}
            </div>
          </div>
          <div class="sku-right">
            <div>{{ money(sku.price) }}</div>
            <div class="muted small">
              可售 {{ sku.available }} / 占用 {{ sku.reserved }} / 已售 {{ sku.sold }}
            </div>
          </div>
        </div>
        <p v-if="!skus.length" class="hint">还没有 SKU，先加一个才能上架。</p>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<style scoped>
.panel {
  padding-top: 12px;
}

.block {
  margin-bottom: 14px;
}

.cat-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.pager {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.sku-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--line);
}

.sku-code {
  font-weight: 600;
  font-size: 13px;
}

.sku-right {
  text-align: right;
  font-size: 13px;
}

.small {
  font-size: 12px;
}
</style>
