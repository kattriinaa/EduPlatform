<script setup>
import { BookOpen, User } from 'lucide-vue-next';
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const router = useRouter()

const userName = computed(() => localStorage.getItem('userName') || 'User')

const goToProfile = () => {
  router.push('/profile')
}
</script>

<template>
  <nav class="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">

        <div class="flex items-center cursor-pointer" @click="router.push('/dashboard')">
          <BookOpen class="w-8 h-8 text-blue-600" />
          <span class="ml-2 text-xl font-semibold text-gray-900">EduPlatform</span>
        </div>

        <div class="flex items-center gap-6">
          <button 
            @click="goToProfile" 
            class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-50 transition-all duration-200 group"
          >
            <div class="flex flex-col items-end mr-1">
              <span class="text-xs text-gray-400 font-medium">My Account</span>
              <span class="text-sm font-bold text-gray-700 group-hover:text-blue-600 transition-colors">
                {{ userName }}
              </span>
            </div>
            
            <div class="w-10 h-10 bg-blue-50 border border-blue-100 rounded-full flex items-center justify-center group-hover:scale-105 transition-transform">
              <User class="w-5 h-5 text-blue-600" />
            </div>
          </button>
        </div>

      </div>
    </div>
  </nav>
</template>