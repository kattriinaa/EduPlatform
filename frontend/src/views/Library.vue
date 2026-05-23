<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { BookOpen, CheckCircle, PlusCircle, Search, Users, Clock } from 'lucide-vue-next'
import DashboardTabs from './DashboardTabs.vue'
import AiChat from './AiChat.vue'

const route = useRoute()

const allCourses = ref([])
const enrolledIds = ref([])
const isLoading = ref(false)
const searchQuery = ref('')

const userId = localStorage.getItem('userId')

const filteredCourses = computed(() => {
  return allCourses.value.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const notEnrolled = !enrolledIds.value.includes(course.id)
    
    return matchesSearch && notEnrolled
  })
})

const fetchAllCourses = async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/courses')
        if (response.ok) {
            allCourses.value = await response.json()
        }
    } catch (err) {
        console.error("Error fetching library:", err)
    }
}

const fetchEnrolledCourses = async () => {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/courses/student/${userId}`)
        if (response.ok) {
            const data = await response.json()
            enrolledIds.value = data.map(course => course.id)
        }
    } catch (err) {
        console.error("Error fetching enrolled status:", err)
    }
}

onMounted(async () => {
    isLoading.value = true
    await Promise.all([fetchAllCourses(), fetchEnrolledCourses()])
    isLoading.value = false
})
</script>
<template>
    <DashboardTabs />
    <div class="min-h-screen bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900">Course Library</h1>
                    <p class="text-gray-500 mt-1">Discover new skills and knowledge</p>
                </div>

                <div class="relative w-full md:w-96">
                    <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input 
                        v-model="searchQuery"
                        type="text" 
                        placeholder="Search for courses..."
                        class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-600 focus:border-transparent outline-none shadow-sm"
                    />
                </div>
            </div>

            <div v-if="isLoading" class="flex justify-center items-center h-64">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>

            <div v-else-if="filteredCourses.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <router-link 
                    v-for="course in filteredCourses" 
                    :key="course.id"
                    :to="`/course/${course.id}`"
                    class="bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-300 flex flex-col"
                >
                    <div class="h-48 bg-blue-100 relative">
                        <img 
                        v-if="course.image" 
                        :src="course.image" 
                        class="w-full h-full object-cover"
                        />
                        <div v-else class="w-full h-full flex items-center justify-center">
                            <BookOpen class="w-12 h-12 text-blue-300" />
                        </div>
                    </div>

                    <div class="p-6 flex-1 flex flex-col">
                        <h3 class="font-semibold text-lg text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                        {{ course.title }}
                        </h3>
                        <p class="text-sm text-gray-600 mb-4">{{ course.teacher }}</p>
                    </div>

                </router-link>
            </div>

            <div v-else class="text-center py-20">
                <p class="text-gray-400 text-lg">No courses found matching "{{ searchQuery }}"</p>
            </div>

        </div>
        <AiChat v-if="route.name && !route.meta.hideNavbar" />
    </div>
</template>