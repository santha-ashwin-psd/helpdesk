<template>
  <Dialog :title="__('Create Service Request')" v-model:open="showDialog">
    <template #default>
      <div class="flex flex-col gap-4">
        <!-- Customer: auto-filled from ticket, read-only -->
        <FormControl
          :label="__('Customer')"
          type="text"
          v-model="customer"
          :disabled="true"
        />

        <!-- Subject: editable, pre-filled from ticket -->
        <FormControl
          :label="__('Subject')"
          type="text"
          v-model="subject"
          :placeholder="__('Enter subject')"
        />

        <!-- Due Date: required -->
        <FormControl
          :label="__('Due Date')"
          type="date"
          v-model="dueDate"
        />

        <!-- Priority: required Select -->
        <FormControl
          :label="__('Priority')"
          type="select"
          v-model="priority"
          :options="priorityOptions"
        />

        <!-- Service Type: required, loaded from server -->
        <FormControl
          :label="__('Service Type')"
          type="select"
          v-model="serviceType"
          :options="serviceTypeOptions"
          :placeholder="serviceTypesResource.loading ? __('Loading…') : __('Select a Service Type')"
        />
      </div>
    </template>

    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Create Service Request')"
        :loading="createServiceRequest.loading"
        @click="handleCreate"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { HDTicket } from "@/types/doctypes";
import { Dialog, FormControl, Button, createResource, toast } from "frappe-ui";
import { ref, computed, watch } from "vue";

interface Props {
  ticket: HDTicket;
}

interface E {
  (event: "update"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<E>();
const showDialog = defineModel<boolean>();

// ── Form state ────────────────────────────────────────────────────────────────
const customer = ref(props.ticket.customer);
const subject = ref(props.ticket.subject);
const dueDate = ref("");
const priority = ref("Medium");
const serviceType = ref("");

watch(
  () => props.ticket,
  (newTicket) => {
    if (newTicket) {
      customer.value = newTicket.customer;
      subject.value = newTicket.subject;
    }
  },
  { immediate: true, deep: true }
);

// ── Priority options (matches Service Request Select field) ───────────────────
const priorityOptions = [
  { label: __("Low"), value: "Low" },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"), value: "High" },
  { label: __("Critical"), value: "Critical" },
];

// ── Service Types: fetch from server ─────────────────────────────────────────
const serviceTypesResource = createResource({
  url: "helpdesk.api.service_request.get_service_types",
  auto: true,
  onSuccess(data: string[]) {
    // Pre-select the first available type
    if (data?.length && !serviceType.value) {
      serviceType.value = data[0];
    }
  },
});

const serviceTypeOptions = computed(() =>
  (serviceTypesResource.data ?? []).map((name: string) => ({
    label: name,
    value: name,
  }))
);

// ── Create resource ───────────────────────────────────────────────────────────
const createServiceRequest = createResource({
  url: "helpdesk.api.service_request.create_service_request",
  makeParams() {
    return {
      hd_customer: customer.value,
      subject: subject.value,
      due_date: dueDate.value,
      ticket_id: props.ticket.name,
      priority: priority.value,
      service_type: serviceType.value,
    };
  },
  validate() {
    if (!subject.value) throw { message: __("Subject is required") };
    if (!dueDate.value) throw { message: __("Due Date is required") };
    if (!serviceType.value) throw { message: __("Service Type is required") };
  },
  onSuccess: (data: any) => {
    toast.success(__("Service Request created successfully."));
    emit("update");
    showDialog.value = false;
    window.open(`/app/service-request/${data.name}`, "_blank");
  },
  onError: (error: any) => {
    toast.error(error.message || __("Failed to create Service Request."));
  },
});

function handleCreate() {
  createServiceRequest.submit();
}
</script>
