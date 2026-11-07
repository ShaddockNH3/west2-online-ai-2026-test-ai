<script setup>
import { NConfigProvider, NDialogProvider, NMessageProvider, dateZhCN, zhCN } from "naive-ui";
import AppShell from "./components/AppShell.vue";
import { themeOverrides } from "./theme";
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
        <app-shell />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
