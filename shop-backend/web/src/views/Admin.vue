<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import { NCard, NTabPane, NTabs } from "naive-ui";
import ActivityPanel from "../components/admin/ActivityPanel.vue";
import FulfillmentPanel from "../components/admin/FulfillmentPanel.vue";
import InventoryPanel from "../components/admin/InventoryPanel.vue";
import JobPanel from "../components/admin/JobPanel.vue";
import OrderPanel from "../components/admin/OrderPanel.vue";
import OverviewPanel from "../components/admin/OverviewPanel.vue";
import ProductPanel from "../components/admin/ProductPanel.vue";

const route = useRoute();
const tab = ref(typeof route.query.tab === "string" ? route.query.tab : "overview");
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">店主后台</h1>
        <p class="page-sub">维护商品与活动、看库存与订单、处理履约和失败的后台任务。</p>
      </div>
    </div>

    <n-card :content-style="{ padding: '6px 20px 20px' }">
      <n-tabs v-model:value="tab" type="line" animated>
        <n-tab-pane name="overview" tab="概览">
          <overview-panel />
        </n-tab-pane>
        <n-tab-pane name="products" tab="商品与类目">
          <product-panel />
        </n-tab-pane>
        <n-tab-pane name="activities" tab="活动">
          <activity-panel />
        </n-tab-pane>
        <n-tab-pane name="inventory" tab="库存">
          <inventory-panel />
        </n-tab-pane>
        <n-tab-pane name="orders" tab="订单">
          <order-panel />
        </n-tab-pane>
        <n-tab-pane name="fulfillment" tab="履约">
          <fulfillment-panel />
        </n-tab-pane>
        <n-tab-pane name="jobs" tab="后台任务">
          <job-panel />
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>
