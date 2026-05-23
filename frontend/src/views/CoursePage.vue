<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Play, FileText, CheckCircle, Circle, Clock, Users, Star, LogOut, Lock, ChevronLeft, Settings, Trash2 } from 'lucide-vue-next'
import AiChat from './AiChat.vue'

const route = useRoute()
const router = useRouter()

const id = route.params.id

const course = ref(null)
const isLoading = ref(true)
const error = ref(null)

const userId = parseInt(localStorage.getItem('userId'))
const userRole = localStorage.getItem('userRole')
const isEnrolled = ref(false)

const showUnenrollModal = ref(false)

const completedLessons = ref([])

const isTeacher = computed(() => localStorage.getItem('userRole') === 'teacher')
const isStudent = computed(() => localStorage.getItem('userRole') === 'student')

const isEditMode = ref(false)

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value
}

const fetchCourse = async () => {
  try {
    isLoading.value = true
    
    const response = await fetch(`http://127.0.0.1:8000/api/courses/${id}`)
    
    if (!response.ok) {
       const errorText = await response.text()
       console.error("Server returned an error:", errorText)
       throw new Error(`Server error: ${response.status}`)
    }

    course.value = await response.json()
  } catch (err) {
    error.value = err.message
    console.error("Error details:", err)
  } finally {
    isLoading.value = false
  }
}

const checkEnrollment = async () => {
  if (userRole !== 'student' || !userId) return
  
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/courses/student/${userId}`)
    if (response.ok) {
      const enrolledCourses = await response.json()
      isEnrolled.value = enrolledCourses.some(c => c.id === parseInt(id))
    }
  } catch (err) {
    console.error("Failed to check enrollment status:", err)
  }
}

const enroll = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/courses/enroll', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId, 
        course_id: parseInt(id) 
      })
    })

    if (response.ok) {
      isEnrolled.value = true
      await fetchCourse()
    }
  } catch (err) {
    alert("Enrollment failed. Please try again.")
  }
}

const unenroll = async () => {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/courses/unenroll', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                user_id: userId, 
                course_id: parseInt(id)
            })
        })

        if (response.ok) {
            isEnrolled.value = false
            await fetchCourse()
        }
    } catch (err) {
        console.error("Unenroll error:", err)
    }
}

const confirmUnenroll = () => {
  showUnenrollModal.value = true
}

const handleUnenroll = async () => {
  await unenroll()
  showUnenrollModal.value = false
}

const goToLesson = (lessonId) => {
  if (isEnrolled.value || userRole === 'teacher') {
    router.push(`/course/${id}/lesson/${lessonId}`)
  } else {
    alert("Please enroll in the course to access lessons.")
  }
}

const nextLessonId = computed(() => {
  if (!course.value || !course.value.modules) return null;
  const allLessons = course.value.modules.flatMap(m => m.lessons || []);
  
  const next = allLessons.find(l => !l.completed);
  return next ? next.id : allLessons[0]?.id;
})

const fetchUserProgress = async () => {
  if (!userId) return
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}`)
    if (response.ok) {
      const data = await response.json()
      completedLessons.value = data.completed_lessons || []
    }
  } catch (err) {
    console.error("Error fetching user progress:", err)
  }
}

const isLessonCompleted = (lessonId) => {
  const courseId = route.params.id; 
  const marker = `${courseId}_${lessonId}`;
  
  return completedLessons.value.includes(marker);
}

const progress = computed(() => {
  if (!course.value || !course.value.modules) return 0
  const allLessons = course.value.modules.flatMap(m => m.lessons || [])
  
  const completedInThisCourse = allLessons.filter(l => 
    completedLessons.value.includes(`${id}_${l.id}`)
  ).length
  
  return allLessons.length > 0 
    ? Math.round((completedInThisCourse / allLessons.length) * 100) 
    : 0
})


const totalDuration = computed(() => {
  if (!course.value?.modules) return '0 min'
  
  const totalMinutes = course.value.modules.flatMap(m => m.lessons || [])
    .reduce((sum, lesson) => {
      const mins = parseInt(lesson.duration) || 0
      return sum + mins
    }, 0)
  
  if (totalMinutes >= 60) {
    const hours = Math.floor(totalMinutes / 60)
    const mins = totalMinutes % 60
    return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`
  }
  return `${totalMinutes} min`
})


const updateCourse = async () => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/courses/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(course.value)
    })
    if (!response.ok) throw new Error("Update failed")
  } catch (err) {
    console.error("Error updating course:", err)
  }
}

const addLesson = (moduleIndex) => {
  const newId = course.value.modules[moduleIndex].lessons.length + 1
  course.value.modules[moduleIndex].lessons.push({
    id: newId,
    title: "New Lesson Name",
    duration: "10 min",
    content: "Write lesson content here"
  })
  updateCourse()
}

const addModule = () => {
  course.value.modules.push({
    title: "New Module Title",
    lessons: []
  })
  updateCourse()
}

const deleteLesson = (moduleIndex, lessonIndex) => {
  if (course.value.modules[moduleIndex].lessons.length > 1) {
    course.value.modules[moduleIndex].lessons.splice(lessonIndex, 1);
  } else {
    alert("Each module must have at least one lesson.");
  }
}

const deleteCourse = async (id) => {
  const finalId = id || route.params.id;
  
  if (!finalId) {
    console.error("Course ID is missing!");
    return;
  }

  if (!confirm('Are you sure you want to delete this course?')) return;

  try {
    const response = await fetch(`http://localhost:8000/api/courses/${finalId}`, { 
      method: 'DELETE' 
    });

    if (response.ok) {
      alert('Course deleted successfully');
      router.push('/dashboard');
    } else {
      const errorData = await response.json();
      alert(`Error: ${errorData.detail}`);
    }
  } catch (error) {
    console.error("Connection error:", error);
  }
}

onMounted(() => {
  fetchCourse()
  checkEnrollment()
  fetchUserProgress()
})
</script>
<template>
  <div v-if="course" class="min-h-screen bg-gray-50">
    <div class="relative h-72 overflow-hidden">
      <img
        :src="course.image"
        :alt="course.title"
        class="w-full h-full object-cover"
      />
      <div class="absolute inset-0 bg-gradient-to-r from-black/70 to-black/50" />
      <button 
        @click="router.push('/dashboard')"
        class="absolute top-4 left-4 flex items-center gap-2 text-white hover:text-blue-300 transition-colors z-10"
      >
        <ChevronLeft class="w-5 h-5" /> Back
      </button>
      <div class="absolute inset-0 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center">
        <div class="text-white">
          <input v-if="isEditMode" 
          v-model="course.title" 
          @change="updateCourse"
          class="text-4xl font-bold w-full border-b border-dashed border-gray-300 focus:border-blue-500 outline-none bg-transparent" />
          <h1 v-else-if="!isEditMode" class="text-4xl font-bold mb-4">{{ course.title }}</h1>
          <div class="flex items-center gap-6 text-sm">
            <div class="flex items-center gap-2">
              <Users class="w-5 h-5" />
              <span>{{ course.students }} students</span>
            </div>
            <div class="flex items-center gap-2">
              <Clock class="w-5 h-5" />
              <span>{{ totalDuration }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Star class="w-5 h-5 fill-yellow-400 text-yellow-400" />
              <span>{{ course.rating }} rating</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-2xl font-semibold text-gray-900 mb-4">About this course</h2>
            <p class="text-gray-700 leading-relaxed mb-4">
              {{ course.full_description || course.description }}
            </p>
          </div>

          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-2xl font-semibold text-gray-900 mb-6">Course Content</h2>
            <div class="space-y-4">
              <div v-for="(module, mIndex) in course.modules" :key="module.id" class="border border-gray-200 rounded-lg overflow-hidden">
                <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
                  <input 
                  v-if="isEditMode" 
                  v-model="module.title" 
                  @change="updateCourse" 
                  class="font-bold text-xl mb-4 bg-transparent border-b border-gray-200 focus:border-blue-400" 
                  />
                  <h3 v-else-if="!isEditMode" class="font-semibold text-gray-900">{{ module.title }}</h3>
                  <button v-if="isEditMode" 
                          @click="addLesson(mIndex)" 
                          class="w-full py-2 mt-2 bg-gray-50 border border-dashed border-gray-300 rounded-lg text-gray-500 hover:bg-gray-100 flex justify-center items-center gap-2">
                    <span>+ Add Lesson</span>
                  </button>
                </div>
                
                <div class="divide-y divide-gray-200">
                  <div
                    v-for="(lesson, lIndex) in module.lessons"
                    :key="lesson.id"
                    @click="goToLesson(lesson.id)"
                    class="px-4 py-3 transition-colors"
                    :class="(isEnrolled || userRole === 'student') 
                      ? 'hover:bg-blue-50 cursor-pointer text-gray-900' 
                      : 'opacity-50 cursor-not-allowed text-gray-400'"
                  >
                    <div class="flex items-center justify-between group">
                      <div class="flex items-center gap-3">
                        <template v-if="userRole === 'teacher'">
                          <Settings class="w-4 h-4 text-gray-400 group-hover:text-blue-500 cursor-move" />
                        </template>
                        
                        <template v-else-if="isEnrolled">
                          <CheckCircle v-if="isLessonCompleted(lesson.id)" class="w-5 h-5 text-green-600" />
                          <Play v-else class="w-4 h-4 text-gray-600" />
                        </template>
                        
                        <template v-else>
                          <Lock class="w-4 h-4 text-gray-400" />
                        </template>

                        <span :class="{'text-gray-400': !isEnrolled && userRole !== 'teacher', 'text-gray-900 font-medium': isEnrolled || userRole === 'teacher'}">
                          {{ lesson.title }}
                        </span>
                      </div>

                      <div class="flex items-center gap-3">
                        <span class="text-sm text-gray-500">{{ lesson.duration }} min</span>
                        
                        <button v-if="isEditMode"  
                                @click.stop="deleteLesson(mIndex, lIndex)" 
                                class="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                title="Delete Lesson"
                        >
                          <Trash2 class="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <button v-if="isEditMode" 
                      @click="addModule" 
                      class="w-full py-4 mt-8 bg-blue-50 border-2 border-dashed border-blue-200 rounded-xl text-blue-600 font-bold hover:bg-blue-100 transition-all">
                + Add New Module
              </button>
            </div>
          </div>
        </div>

        <div class="lg:col-span-1">
          <div class="bg-white rounded-lg shadow p-6 sticky top-24">
            <h3 class="font-semibold text-gray-900 mb-4">teacher</h3>
            <div class="flex items-center gap-3 mb-6">
              <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span class="text-blue-600 font-semibold">
                  {{ course.teacher?.split(' ').map(n => n[0]).join('') || '?' }}
                </span>
              </div>
              <div>
                <p class="font-medium text-gray-900">{{ course.teacher }}</p>
                <p class="text-sm text-gray-600">Course teacher</p>
              </div>
            </div>

            <div class="border-t border-gray-200 pt-6">
              <h3 class="font-semibold text-gray-900 mb-4">Course Stats</h3>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-gray-600">Enrolled</span>
                  <span class="font-medium text-gray-900">{{ course.students }} students</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Duration</span>
                  <span class="font-medium text-gray-900">{{ course.duration }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600">Rating</span>
                  <span class="font-medium text-gray-900">{{ course.rating }}/5.0</span>
                </div>
              </div>
            </div>

            <div v-if="userRole === 'student'" class="flex gap-4 mt-6">
              <button 
                v-if="isEnrolled"
                @click="goToLesson(nextLessonId)"
                class="flex-1 bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100"
              >
                {{ progress === 100 ? 'Review Course' : 'Continue Learning' }}
              </button>

              <button 
                v-else
                @click="enroll" 
                class="flex-1 bg-green-600 text-white py-3 rounded-xl font-bold hover:bg-green-700 transition-all shadow-lg shadow-green-100"
              >
                Enroll Now
              </button>

              <button 
                v-if="isEnrolled"
                @click="confirmUnenroll" 
                class="px-4 py-3 border border-gray-200 text-gray-400 hover:text-red-600 rounded-xl"
              >
                <LogOut class="w-5 h-5" />
              </button>
            </div>

            <div v-if="showUnenrollModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div class="absolute inset-0 bg-gray-900/50 backdrop-blur-sm" @click="showUnenrollModal = false"></div>

              <div class="relative bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
                <h3 class="text-lg font-bold mb-2">Leave this course?</h3>
                <p class="text-gray-500 mb-6">Are you sure you want to unenroll?</p>

                <div class="flex gap-3">
                  <button @click="showUnenrollModal = false" class="flex-1 py-2 bg-gray-100 rounded-lg">
                    Cancel
                  </button>
                  <button @click="handleUnenroll" class="flex-1 py-2 bg-red-600 text-white rounded-lg">
                    Yes, Unenroll
                  </button>
                </div>
              </div>
            </div>
            <div v-if="userRole === 'teacher'" class="py-5 flex flex-col gap-3"> 
              <button 
                @click="toggleEditMode"
                class="w-full py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg"
                :class="isEditMode ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-800 text-white hover:bg-black'"
              >
                <Settings class="w-5 h-5" />
                {{ isEditMode ? 'Save' : 'Edit Course' }}
              </button>

              <button v-if="isEditMode"  
                @click.stop="deleteCourse(courseId)" 
                class="w-full py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg text-gray-400 hover:text-red-500 hover:bg-red-50 border border-transparent hover:border-red-100"
                title="Delete Course"
              >
                <Trash2 class="w-4 h-4" /> Delete Course </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <AiChat v-if="route.name && !route.meta.hideNavbar" />
  </div>
</template>
<style></style>