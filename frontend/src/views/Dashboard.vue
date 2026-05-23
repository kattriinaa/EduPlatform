<script setup>
import { useRoute } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import { BookOpen, Clock, Users, TrendingUp, FileText, PlusCircle, Trash2 } from 'lucide-vue-next'
import DashboardTabs from './DashboardTabs.vue'
import AiChat from './AiChat.vue'

const route = useRoute()

const completedLessons = ref([])

const isTeacher = computed(() => {
  const role = route.query.role || localStorage.getItem('userRole')
  return role === 'teacher'
})

const isStudent = computed(() => {
  const role = route.query.role || localStorage.getItem('userRole')
  return role === 'student' || !role
})

const courses = ref([])

const fetchCourses = async () => {
  try {
    const userId = localStorage.getItem('userId')
    const role = localStorage.getItem('userRole')
    
    const url = role === 'student' 
      ? `http://127.0.0.1:8000/api/courses/student/${userId}`
      : `http://127.0.0.1:8000/api/courses/teacher/${userId}`
    
    const response = await fetch(url)
    if (!response.ok) throw new Error('Помилка мережі')
    
    courses.value = await response.json()
  } catch (error) {
    console.error("Не вдалося завантажити курси:", error)
  }
}

const fetchUserData = async () => {
  const userId = localStorage.getItem('userId')
  if (!userId) return
  
  const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}`)
  if (response.ok) {
    const data = await response.json()
    completedLessons.value = data.completed_lessons || []
  }
}

const progress = (course) => {
  if (!course.modules) return 0
  const allLessons = course.modules.flatMap(m => m.lessons || [])
  if (allLessons.length === 0) return 0

  const completedInThisCourse = allLessons.filter(l => {
    const marker = `${course.id}_${l.id}`
    const isDone = completedLessons.value.includes(marker)
    return isDone
  }).length

  const percent = Math.round((completedInThisCourse / allLessons.length) * 100)
  return percent
}

const deleteCourse = async (courseId, event) => {
  event.preventDefault();
  event.stopPropagation();

  if (!confirm('Ви впевнені, що хочете видалити цей курс? Всі дані будуть втрачені.')) {
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:8000/api/courses/${courseId}`, {
      method: 'DELETE',
    });

    if (response.ok) {
      courses.value = courses.value.filter(c => c.id !== courseId);
      alert('Курс успішно видалено');
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Помилка при видаленні');
    }
  } catch (error) {
    console.error("Не вдалося видалити курс:", error);
    alert('Помилка: ' + error.message);
  }
}

onMounted(() => {
  fetchCourses()
  fetchUserData()
})
</script>
<template>
  <DashboardTabs />
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">My Courses</h1>
        <div v-if = "isStudent">
          <p class="text-gray-600 mt-2">Continue your learning journey</p>
        </div>
        <div v-else-if = "isTeacher">
          <p class="text-gray-600 mt-2">Manage your courses and students</p>
        </div>
      </div>
      <div class="py-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <router-link 
          v-for="course in courses" 
          :key="course.id"
          :to="`/course/${course.id}`"
          class="relative bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden group"
        >
          <div class="relative h-48 overflow-hidden">
            <img
              :src="course.image"
              :alt="course.title"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          </div>

          <div class="p-6">
            <h3 class="font-semibold text-lg text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
              {{ course.title }}
            </h3>
            <p class="text-sm text-gray-600 mb-4">{{ course.teacher }}</p>

            <div class="space-y-3">
              <div class="flex items-center justify-between text-sm text-gray-600">
                <div class="flex items-center gap-1">
                  <Users class="w-4 h-4" />
                    <span>{{ course.students }} students</span>
                </div>
                <button 
                  v-if="isTeacher"
                  @click="deleteCourse(course.id, $event)"
                  class="absolute right-3 z-10 p-2 bg-red-100 text-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 hover:text-white"
                  title="Delete Course"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>

              <div v-if="isStudent">
                <div class="flex justify-between text-sm mb-1">
                  <span class="text-gray-600">Progress</span>
                  <span class="font-medium text-gray-900">{{ progress(course) }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all"
                    :style="{ width: progress(course) + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </router-link>
      </div>
      <router-link 
        v-if="isTeacher"
        to="/instructor/create-course" 
        class="bg-blue-600 text-white px-6 py-3 rounded-2xl font-bold flex items-center gap-2 hover:bg-blue-700 transition-all shadow-lg"
      >
        <PlusCircle class="w-5 h-5" />
        Create New Course
      </router-link>
    </div>
    <AiChat v-if="route.name && !route.meta.hideNavbar" />
  </div>
</template>
<style></style>