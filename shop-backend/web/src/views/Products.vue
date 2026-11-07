<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NButton,
  NCard,
  NEmpty,
  NInput,
  NPagination,
  NSelect,
  NSpace,
  NSpin,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../api";
import { store } from "../store";

const router = useRouter();
const message = useMessage();

const loading = ref(false);
const products = ref([]);
const categories = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = 12;
const categoryId = ref(null);
const keyword = ref("");

const categoryOptions = computed(() => [
  { label: "全部类目", value: null },
  ...categories.value.map((item) => ({ label: item.name, value: item.id })),
]);

async function load() {
  loading.value = true;
  try {
    const params = new URLSearchParams({ page: String(page.value), pageSize: String(pageSize) });
    if (categoryId.value) params.set("categoryId", String(categoryId.value));
    if (keyword.value.trim()) params.set("keyword", keyword.value.trim());
    const data = await http.get(`/products?${params.toString()}`);
    products.value = data.items;
    total.value = data.total;
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function loadCategories() {
  try {
    const data = await http.get("/categories");
    categories.value = data.items;
  } catch {
    categories.value = [];
  }
}

function search() {
  page.value = 1;
  load();
}

function onCategory(value) {
  categoryId.value = value;
  page.value = 1;
  load();
}

function openProduct(id) {
  router.push(`/products/${id}`);
}

async function quickAdd(item) {
  if (!store.user) {
    router.push({ name: "login", query: { redirect: `/products/${item.id}` } });
    return;
  }
  router.push(`/products/${item.id}`);
}

function priceLabel(item) {
  if (!item.minPrice) return "暂无报价";
  if (item.minPrice === item.maxPrice) return money(item.minPrice);
  return `${money(item.minPrice)} 起`;
}

onMounted(() => {
  loadCategories();
  load();
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">工作室周边</h1>
        <p class="page-sub">文化衫、帆布袋、徽章。下单后可以在「我的订单」里看支付与发货进度。</p>
      </div>
      <n-space>
        <n-select
          :value="categoryId"
          :options="categoryOptions"
          style="width: 150px"
          placeholder="类目"
          @update:value="onCategory"
        />
        <n-input
          v-model:value="keyword"
          placeholder="搜索商品名称"
          clearable
          style="width: 220px"
          @keyup.enter="search"
        />
        <n-button type="primary" secondary @click="search">搜索</n-button>
      </n-space>
    </div>

    <n-spin :show="loading">
      <div v-if="products.length" class="grid-products">
        <n-card
          v-for="item in products"
          :key="item.id"
          hoverable
          class="product-card"
          @click="openProduct(item.id)"
        >
          <div class="thumb">{{ item.name.slice(0, 1) }}</div>
          <div class="product-body">
            <div class="row-between">
              <span class="product-name">{{ item.name }}</span>
              <n-tag v-if="item.hasActivity" size="small" type="error" :bordered="false">
                活动
              </n-tag>
            </div>
            <div class="muted product-cat">{{ item.categoryName }}</div>
            <div class="row-between">
              <span class="price">{{ priceLabel(item) }}</span>
              <span class="muted stock">库存 {{ item.stockAvailable }}</span>
            </div>
            <n-button size="small" type="primary" tertiary block @click.stop="quickAdd(item)">
              选规格购买
            </n-button>
          </div>
        </n-card>
      </div>
      <n-empty v-else description="没有找到商品" class="empty" />
    </n-spin>

    <div v-if="total > pageSize" class="pager">
      <n-pagination
        v-model:page="page"
        :page-size="pageSize"
        :item-count="total"
        @update:page="load"
      />
    </div>
  </div>
</template>

<style scoped>
.product-card {
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease;
}

.product-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.product-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-name {
  font-weight: 600;
  font-size: 15px;
}

.product-cat {
  font-size: 12px;
}

.stock {
  font-size: 12px;
}

.pager {
  display: flex;
  justify-content: center;
  margin-top: 26px;
}
</style>
