
<template>
  <Dialog :title="__('Create Service Request')" v-model:open="showDialog">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="error" />
        <!-- Customer: auto-filled from ticket, read-only if present; search-and-select if empty -->
        <FormControl
          v-if="ticket.customer"
          :label="__('Customer')"
          type="text"
          v-model="customer"
          :disabled="true"
        />
        <Link
          v-else
          :label="__('Customer')"
          doctype="HD Customer"
          v-model="customer"
          :required="true"
          :placeholder="__('Select a Customer')"
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
import { Link } from "@/components";
import { Dialog, FormControl, Button, createResource, toast, ErrorMessage } from "frappe-ui";
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
const error = ref("");

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
  beforeSubmit() {
    error.value = "";
  },
  validate() {
    if (!customer.value) throw { message: __("Customer is required") };
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
  onError: (err: any) => {
    console.log("=== SERVICE REQUEST ERROR ===");
    console.log("err:", JSON.stringify(err, null, 2));
    console.log("err.message:", err?.message);
    console.log("err.exc_type:", err?.exc_type);
    console.log("err._server_messages:", err?._server_messages);
    console.log("err.exception:", err?.exception);
    console.log("err.messages:", err?.messages);
    console.log("============================");
    const msg = parseFrappeError(err);
    error.value = msg;
    toast.error(msg);
  },
});

/**
 * Frappe REST errors arrive in one of two shapes:
 *
 * Shape A – validate() threw synchronously:
 *   err = { message: "Customer is required" }
 *
 * Shape B – server returned an HTTP error:
 *   err.exc_type  = "ValidationError" | "MandatoryError" | ...
 *   err._server_messages = JSON string of an array of JSON strings, each:
 *     { message: "...", title: "...", indicator: "..." }
 *
 * We prefer Shape A as-is; for Shape B we unwrap _server_messages.
 * If nothing useful is found we fall back to a generic message.
 */
function parseFrappeError(err: any): string {
  const NOISE = new Set(["ValidationError", "MandatoryError", "Error", ""]);

  // Shape A: thrown directly from validate()
  if (err?.message && !NOISE.has(err.message) && !err.exc_type) {
    return err.message;
  }

  // Shape B: server error — dig into _server_messages
  if (err?._server_messages) {
    try {
      const outer: string[] = JSON.parse(err._server_messages);
      for (const raw of outer) {
        const inner = JSON.parse(raw);
        const msg: string = inner?.message ?? "";
        if (msg && !NOISE.has(msg)) return msg;
      }
    } catch (_) { /* fall through */ }
  }

  // Last resort: exc_type gives us at least a category
  if (err?.exc_type && !NOISE.has(err.exc_type)) return err.exc_type;

  return __("Failed to create Service Request.");
}

function handleCreate() {
  error.value = "";
  console.log("=== SUBMIT VALUES ===");
  console.log("customer.value:", customer.value);
  console.log("subject.value:", subject.value);
  console.log("dueDate.value:", dueDate.value);
  console.log("ticket.customer:", props.ticket.customer);
  console.log("ticket keys:", Object.keys(props.ticket));
  console.log("====================");
  try {
    createServiceRequest.submit();
  } catch (e: any) {
    const msg = parseFrappeError(e);
    error.value = msg;
    toast.error(msg);
  }
}
</script>