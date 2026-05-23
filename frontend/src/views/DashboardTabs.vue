<script setup>
import { LayoutGrid, Library, Calendar, FileText, ClipboardCheck } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { ref, onMounted, computed } from 'vue';

const route = useRoute();
const userRole = computed(() => route.query.role || localStorage.getItem('userRole'));

const pendingCount = ref(0);

const isActive = (path) => route.path === path

const fetchPendingCount = async () => {
    if (userRole.value === 'teacher') {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/submissions/pending-count');
            if (response.ok) {
                const data = await response.json();
                pendingCount.value = data.count;
            }
        } catch (err) {
            console.error("Error fetching pending count:", err);
        }
    }
};

onMounted(fetchPendingCount);
</script>
<template>
    <div class="bg-white border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center gap-8 h-12">
                
                <router-link 
                :to="{ path: '/dashboard', query: { role: userRole } }"
                class="flex items-center gap-2 h-full px-1 border-b-2 transition-all duration-200 text-sm font-medium"
                :class="isActive('/dashboard') 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                >
                <LayoutGrid class="w-4 h-4" />
                <span>Dashboard</span>
                </router-link>

                <router-link 
                    v-if="userRole === 'student'"
                    to="/assignments"
                    class="flex items-center gap-2 h-full px-1 border-b-2 transition-all duration-200 text-sm font-medium"
                    :class="isActive('/assignments') ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                >
                    <FileText class="w-4 h-4" />
                    <span>My Assignments</span>
                </router-link>

                <router-link
                v-if="userRole === 'student'"
                to="/library"
                class="flex items-center gap-2 h-full px-1 border-b-2 transition-all duration-200 text-sm font-medium"
                :class="isActive('/library') 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                >
                <Library class="w-4 h-4" />
                <span>Library</span>
                </router-link>

                <router-link 
                to="/calendar"
                class="flex items-center gap-2 h-full px-1 border-b-2 transition-all duration-200 text-sm font-medium"
                :class="isActive('/calendar') 
                    ? 'border-blue-600 text-blue-600' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                >
                <Calendar class="w-4 h-4" />
                <span>Calendar</span>
                </router-link>

                <router-link 
                    v-if="userRole === 'teacher'"
                    to="/instructor/review"
                    class="relative flex items-center gap-2 h-full px-1 border-b-2 transition-all duration-200 text-sm font-medium"
                    :class="isActive('/instructor/review') ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                >
                    <ClipboardCheck class="w-4 h-4" />
                    <span>Review Tasks</span>
                    
                    <span v-if="pendingCount > 0" class="absolute -top-1 -right-2 flex h-4 w-4">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-4 w-4 bg-red-500 text-[10px] text-white items-center justify-center font-bold">
                            {{ pendingCount }}
                        </span>
                    </span>
                </router-link>

            </div>
        </div>
    </div>
</template>
<style></style>