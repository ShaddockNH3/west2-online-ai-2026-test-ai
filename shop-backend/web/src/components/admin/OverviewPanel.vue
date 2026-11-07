<script setup>
import { onMounted, ref } from "vue";
import { NCard, NGi, NGrid, NStatistic, NTable, NTag } from "naive-ui";
import { http, money } from "../../api";
import { statusText } from "../../theme";

const data = ref(null);
const error = ref("");

async function load() {
  try {
    data.value = await http.get("/admin/overview");
  } catch (err) {
    error.value = err.message;
  }
}

onMounted(load);
</script>

<template>
  <div class="overview">
    <p v-if="error" class="muted">{{ error }}</p>
    <template v-if="data">
      <n-grid :cols="4" :x-gap="12" :y-gap="12" responsive="screen" item-responsive>
        <n-gi span="4 s:2 m:1">
          <n-card size="small">
            <n-statistic label="已收款金额" :value="money(data.paidAmount)" />
          </n-card>
        </n-gi>
        <n-gi span="4 s:2 m:1">
          <n-card size="small">
            <n-statistic label="待处理履约" :value="data.pendingFulfillments" />
          </n-card>
        </n-gi>
        <n-gi span="4 s:2 m:1">
          <n-card size="small">
            <n-statistic label="待执行任务" :value="data.pendingJobs" />
          </n-card>
        </n-gi>
        <n-gi span="4 s:2 m:1">
          <n-card size="small">
            <n-statistic label="失败任务" :value="data.failedJobs">
              <template #suffix>
                <n-tag v-if="data.failedJobs" size="small" type="error" :bordered="false">需处理</n-tag>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <div class="split">
        <n-card title="订单状态分布" size="small">
          <div v-if="Object.keys(data.ordersByStatus).length" class="status-list">
            <div v-for="(count, status) in data.ordersByStatus" :key="status" class="status-row">
              <span>{{ statusText[status] || status }}</span>
              <strong>{{ count }}</strong>
            </div>
          </div>
          <p v-else class="muted">还没有订单</p>
        </n-card>

        <n-card title="库存告急（可售 ≤ 5）" size="small">
          <n-table v-if="data.lowStockSkus.length" :single-line="false" size="small">
            <thead>
              <tr>
                <th>商品</th>
                <th>SKU</th>
                <th>可售</th>
                <th>占用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.lowStockSkus" :key="row.skuId">
                <td>{{ row.productName }}</td>
                <td>{{ row.skuCode }}</td>
                <td>{{ row.available }}</td>
                <td>{{ row.reserved }}</td>
              </tr>
            </tbody>
          </n-table>
          <p v-else class="muted">库存都还充足</p>
        </n-card>
      </div>
    </template>
  </div>
</template>

<style scoped>
.overview {
  padding-top: 12px;
}

.split {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 14px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px dashed var(--line);
}

@media (max-width: 900px) {
  .split {
    grid-template-columns: 1fr;
  }
}
</style>
