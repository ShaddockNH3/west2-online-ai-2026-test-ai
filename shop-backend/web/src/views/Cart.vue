<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NButton,
  NCard,
  NCheckbox,
  NEmpty,
  NInputNumber,
  NPopconfirm,
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
const cart = ref({ items: [], totalAmount: "0.00", totalQuantity: 0 });
const selected = ref(new Set());

const purchasableIds = computed(() =>
  cart.value.items.filter((item) => item.purchasable).map((item) => item.id),
);

const allSelected = computed(
  () =>
    purchasableIds.value.length > 0 &&
    purchasableIds.value.every((id) => selected.value.has(id)),
);

const selectedItems = computed(() =>
  cart.value.items.filter((item) => selected.value.has(item.id)),
);

const selectedAmount = computed(() => {
  const cents = selectedItems.value.reduce(
    (sum, item) => sum + Math.round(Number(item.price) * 100) * item.quantity,
    0,
  );
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, "0")}`;
});

async function load() {
  loading.value = true;
  try {
    cart.value = await http.get("/cart/items");
    const next = new Set(selected.value);
    for (const item of cart.value.items) {
      if (item.purchasable && next.size === 0) next.add(item.id);
    }
    for (const id of [...next]) {
      if (!cart.value.items.some((item) => item.id === id && item.purchasable)) {
        next.delete(id);
      }
    }
    selected.value = next;
    await refreshCart();
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

function toggle(id, checked) {
  const next = new Set(selected.value);
  if (checked) next.add(id);
  else next.delete(id);
  selected.value = next;
}

function toggleAll(checked) {
  selected.value = new Set(checked ? purchasableIds.value : []);
}

async function changeQuantity(item, value) {
  if (!value) return;
  try {
    await http.patch(`/cart/items/${item.id}`, { quantity: value });
    await load();
  } catch (error) {
    message.error(error.message);
    await load();
  }
}

async function remove(item) {
  try {
    await http.del(`/cart/items/${item.id}`);
    message.success("已移除");
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

function checkout() {
  if (!selectedItems.value.length) {
    message.warning("先选要结算的商品");
    return;
  }
  store.checkoutIds = selectedItems.value.map((item) => item.id);
  router.push("/checkout");
}

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">购物车</h1>
        <p class="page-sub">加入购物车不代表下单，可以只挑其中几件结算。</p>
      </div>
      <n-tag :bordered="false" type="info">共 {{ cart.totalQuantity }} 件</n-tag>
    </div>

    <n-spin :show="loading">
      <n-card v-if="cart.items.length">
        <div class="row-between list-head">
          <n-checkbox :checked="allSelected" @update:checked="toggleAll">全选可购买商品</n-checkbox>
          <span class="muted">单价随活动变化，结算时以服务端为准</span>
        </div>

        <div v-for="item in cart.items" :key="item.id" class="cart-row">
          <n-checkbox
            :checked="selected.has(item.id)"
            :disabled="!item.purchasable"
            @update:checked="(checked) => toggle(item.id, checked)"
          />
          <div class="thumb small">{{ item.productName.slice(0, 1) }}</div>
          <div class="cart-main">
            <div class="row-between">
              <span class="cart-name">{{ item.productName }}</span>
              <n-tag v-if="item.activityName" size="small" type="error" :bordered="false">
                {{ item.activityName }}
              </n-tag>
            </div>
            <div class="muted spec">
              {{ Object.values(item.specs || {}).join(" / ") || "默认规格" }}
            </div>
            <div v-if="!item.purchasable" class="warn">{{ item.reason }}</div>
          </div>
          <div class="cart-price">
            <div class="price">{{ money(item.price) }}</div>
            <div v-if="item.activityName" class="muted strike">
              {{ money(item.originalPrice) }}
            </div>
          </div>
          <n-input-number
            :value="item.quantity"
            :min="1"
            :max="item.availableStock || 1"
            size="small"
            style="width: 96px"
            :disabled="!item.purchasable"
            @update:value="(value) => changeQuantity(item, value)"
          />
          <div class="cart-subtotal">{{ money(item.subtotal) }}</div>
          <n-popconfirm @positive-click="remove(item)">
            <template #trigger>
              <n-button text type="error" size="small">移除</n-button>
            </template>
            确定把「{{ item.productName }}」移出购物车？
          </n-popconfirm>
        </div>

        <div class="cart-foot">
          <div>
            已选 <strong>{{ selectedItems.length }}</strong> 项，合计
            <span class="price big">{{ money(selectedAmount) }}</span>
          </div>
          <n-space>
            <n-button @click="router.push('/')">继续逛逛</n-button>
            <n-button type="primary" size="large" @click="checkout">去结算</n-button>
          </n-space>
        </div>
      </n-card>

      <n-empty v-else description="购物车空空的" class="empty">
        <template #extra>
          <n-button type="primary" @click="router.push('/')">去挑点周边</n-button>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<style scoped>
.list-head {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
  font-size: 13px;
}

.cart-row {
  display: grid;
  grid-template-columns: 24px 64px 1fr 100px 110px 100px 56px;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px dashed var(--line);
}

.thumb.small {
  height: 64px;
  font-size: 22px;
  border-radius: 8px;
}

.cart-name {
  font-weight: 600;
}

.spec {
  font-size: 12px;
  margin-top: 4px;
}

.warn {
  margin-top: 6px;
  color: #d92d20;
  font-size: 12px;
}

.cart-price {
  text-align: right;
}

.strike {
  font-size: 12px;
  text-decoration: line-through;
}

.cart-subtotal {
  text-align: right;
  font-weight: 600;
}

.cart-foot {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.big {
  font-size: 22px;
}

@media (max-width: 900px) {
  .cart-row {
    grid-template-columns: 24px 1fr;
    grid-auto-rows: min-content;
  }

  .thumb.small,
  .cart-price,
  .cart-subtotal {
    display: none;
  }
}
</style>
