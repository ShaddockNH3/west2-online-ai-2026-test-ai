<script setup>
import { onMounted, ref } from "vue";
import {
  NButton,
  NCard,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NPopconfirm,
  NSpace,
  NSpin,
  NSwitch,
  NTag,
  useMessage,
} from "naive-ui";
import { http } from "../api";

const message = useMessage();

const loading = ref(false);
const addresses = ref([]);
const visible = ref(false);
const saving = ref(false);
const editingId = ref(null);
const form = ref({ receiver: "", phone: "", detail: "", isDefault: false });

async function load() {
  loading.value = true;
  try {
    const data = await http.get("/addresses");
    addresses.value = data.items;
  } catch (error) {
    message.error(error.message);
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingId.value = null;
  form.value = { receiver: "", phone: "", detail: "", isDefault: false };
  visible.value = true;
}

function openEdit(item) {
  editingId.value = item.id;
  form.value = {
    receiver: item.receiver,
    phone: item.phone,
    detail: item.detail,
    isDefault: item.isDefault,
  };
  visible.value = true;
}

async function save() {
  if (!form.value.receiver || !form.value.phone || !form.value.detail) {
    message.warning("收货人、电话和详细地址都要填");
    return;
  }
  saving.value = true;
  try {
    if (editingId.value) {
      await http.patch(`/addresses/${editingId.value}`, form.value);
      message.success("地址已更新");
    } else {
      await http.post("/addresses", form.value);
      message.success("地址已添加");
    }
    visible.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  } finally {
    saving.value = false;
  }
}

async function remove(item) {
  try {
    await http.del(`/addresses/${item.id}`);
    message.success("已删除");
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function setDefault(item) {
  try {
    await http.put(`/addresses/${item.id}/default`, {});
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1 class="page-title">收货地址</h1>
        <p class="page-sub">可以保存多个地址，结算时挑一个用。历史订单保存的是当时的地址快照。</p>
      </div>
      <n-button type="primary" @click="openCreate">新增地址</n-button>
    </div>

    <n-spin :show="loading">
      <div v-if="addresses.length" class="grid">
        <n-card v-for="item in addresses" :key="item.id" class="card">
          <div class="row-between">
            <div class="who">
              {{ item.receiver }}
              <span class="muted phone">{{ item.phone }}</span>
            </div>
            <n-tag v-if="item.isDefault" size="small" type="success" :bordered="false">
              默认
            </n-tag>
          </div>
          <div class="detail">{{ item.detail }}</div>
          <div class="actions">
            <n-space size="small">
              <n-button v-if="!item.isDefault" size="small" text type="primary" @click="setDefault(item)">
                设为默认
              </n-button>
              <n-button size="small" text @click="openEdit(item)">编辑</n-button>
              <n-popconfirm @positive-click="remove(item)">
                <template #trigger>
                  <n-button size="small" text type="error">删除</n-button>
                </template>
                确定删除这条地址？
              </n-popconfirm>
            </n-space>
          </div>
        </n-card>
      </div>
      <n-empty v-else description="还没有收货地址" class="empty">
        <template #extra>
          <n-button type="primary" @click="openCreate">新增一条</n-button>
        </template>
      </n-empty>
    </n-spin>

    <n-modal v-model:show="visible" preset="card" :title="editingId ? '编辑地址' : '新增地址'" style="width: 460px">
      <n-form label-placement="top">
        <n-form-item label="收货人">
          <n-input v-model:value="form.receiver" placeholder="真实姓名或称呼" />
        </n-form-item>
        <n-form-item label="联系电话">
          <n-input v-model:value="form.phone" placeholder="手机号" />
        </n-form-item>
        <n-form-item label="详细地址">
          <n-input
            v-model:value="form.detail"
            type="textarea"
            placeholder="省市区 + 楼栋门牌"
            :maxlength="255"
            show-count
          />
        </n-form-item>
        <n-form-item label="设为默认地址">
          <n-switch v-model:value="form.isDefault" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="visible = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="save">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.who {
  font-weight: 600;
}

.phone {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 400;
}

.detail {
  margin-top: 10px;
  color: #334155;
  line-height: 1.7;
  min-height: 44px;
}

.actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}
</style>
