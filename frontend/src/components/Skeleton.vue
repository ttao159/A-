<template>
  <div v-for="i in rows" :key="i" class="card">
    <div class="sk sk-title"></div>
    <div class="sk sk-row"></div>
    <div class="sk sk-row short"></div>
    <div class="sk sk-row"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ rows?: number }>()
</script>
