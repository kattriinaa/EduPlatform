<script setup>
import { useRoute } from 'vue-router'
import Navigation from './views/Navigation.vue'

const route = useRoute()
</script>

<template>
    <div class="min-h-screen bg-gray-50">
    <Navigation v-if="route.name && !route.meta.hideNavbar" /> 
    <router-view /> 
  </div>
</template>

<style scoped></style>
