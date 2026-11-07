<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  NAlert,
  NBreadcrumb,
  NBreadcrumbItem,
  NButton,
  NCard,
  NInputNumber,
  NRadioButton,
  NRadioGroup,
  NSkeleton,
  NSpace,
  NTag,
  useMessage,
} from "naive-ui";
import { http, money } from "../api";
import { refreshCart, store } from "../store";

const route = useRoute();
const router = useRouter();
const message = useMessage();

const loading = ref(true);
const product = ref(null);
const selectedSkuId = ref(null);
const quantity = ref(1);
const submitting = ref(false);

const selectedSku = computed(
  () => product.value?.skus.find((sku) => sku.id === selectedSkuId.value) || null,
);

function specText(specs) {
  const values = Object.values(specs || {});
  return values.length ? values.join(" / ") : "默认规格";
}

async function load() {
  loading.value = true;
  try {
    product.value = await http.get(`/products/${route.params.id}`);
    const firstSellable = product.value.skus.find((sku) => sku.purchasable);
    selectedSkuId.value = (firstSellable || product.value.skus[0])?.id || null;
  } catch (error) {
    message.error(error.message);
    router.push("/");
  } finally {
    loading.value = false;
  }
}

watch(selectedSkuId, () => {
  quantity.value = 1;
});

async function addToCart() {
  if (!selectedSku.value) return;
  if (!store.user) {
    router.push({ name: "login", query: { redirect: route.fullPath } });
    return;
  }
  submitting.value = true;
  try {
    await http.post("/cart/items", {
      skuId: selectedSku.value.id,
      quantity: quantity.value,
    });
    await refreshCart();
    message.success("已加入购物车");
  } catch (error) {
    message.error(error.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <n-breadcrumb class="crumb">
      <n-breadcrumb-item @click="router.push('/')">全部商品</n-breadcrumb-item>
      <n-breadcrumb-item v-if="product">{{ product.category?.name }}</n-breadcrumb-item>
      <n-breadcrumb-item v-if="product">{{ product.name }}</n-breadcrumb-item>
    </n-breadcrumb>

    <n-skeleton v-if="loading" height="360px" :sharp="false" />
    <div v-else-if="product" class="detail">
      <div class="visual">
        <div class="thumb big">{{ product.name.slice(0, 1) }}</div>
        <div class="visual-note muted">示意图，实物以工作室群公告为准</div>
      </div>

      <n-card class="info">
        <div class="row-between">
          <h1 class="name">{{ product.name }}</h1>
          <n-tag v-if="product.status === 'ON_SALE'" type="success" :bordered="false">在售</n-tag>
        </div>
        <p class="desc">{{ product.description || "暂无介绍" }}</p>
        <div class="muted cat">{{ product.category?.name }}</div>

        <n-alert v-if="selectedSku?.activityName" type="error" :show-icon="false" class="activity">
          正在参加「{{ selectedSku.activityName }}」，活动价 {{ money(selectedSku.price) }}，
          原价 {{ money(selectedSku.originalPrice) }}。
        </n-alert>

        <div class="block">
          <div class="block-label">选择规格</div>
          <n-radio-group v-model:value="selectedSkuId">
            <n-space>
              <n-radio-button
                v-for="sku in product.skus"
                :key="sku.id"
                :value="sku.id"
                :disabled="!sku.purchasable"
              >
                {{ specText(sku.specs) }}
                <span class="sku-price">{{ money(sku.price) }}</span>
              </n-radio-button>
            </n-space>
          </n-radio-group>
        </div>

        <div class="block">
          <div class="block-label">数量</div>
          <n-input-number
            v-model:value="quantity"
            :min="1"
            :max="selectedSku?.availableStock || 1"
            style="width: 170px"
          />
          <span class="muted stock-note">
            可售 {{ selectedSku?.availableStock ?? 0 }} 件
          </span>
        </div>

        <div class="buy">
          <div class="price-line">
            <span class="price big-price">{{ money(selectedSku?.price) }}</span>
            <span v-if="selectedSku?.activityName" class="muted original">
              原价 {{ money(selectedSku?.originalPrice) }}
            </span>
          </div>
          <n-button
            type="primary"
            size="large"
            :loading="submitting"
            :disabled="!selectedSku?.purchasable"
            @click="addToCart"
          >
            加入购物车
          </n-button>
        </div>
      </n-card>
    </div>
  </div>
</template>

<style scoped>
.crumb {
  margin-bottom: 16px;
}

.detail {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 24px;
  align-items: start;
}

.thumb.big {
  height: 320px;
  font-size: 72px;
  border-radius: 14px;
}

.visual-note {
  margin-top: 10px;
  font-size: 12px;
  text-align: center;
}

.name {
  margin: 0;
  font-size: 24px;
}

.desc {
  margin: 12px 0 8px;
  line-height: 1.8;
  color: #334155;
}

.cat {
  font-size: 12px;
}

.activity {
  margin: 16px 0;
}

.block {
  margin-top: 20px;
}

.block-label {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #334155;
}

.sku-price {
  margin-left: 6px;
  font-size: 12px;
  opacity: 0.8;
}

:deep(.n-input-number .n-input__input-el) {
  text-align: center;
}

.stock-note {
  margin-left: 12px;
  font-size: 12px;
}

.buy {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.big-price {
  font-size: 26px;
}

.original {
  margin-left: 10px;
  font-size: 13px;
  text-decoration: line-through;
}

@media (max-width: 860px) {
  .detail {
    grid-template-columns: 1fr;
  }
}
</style>
