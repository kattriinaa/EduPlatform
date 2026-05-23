<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Calendar, Clock, Video, FileText, CheckCircle } from 'lucide-vue-next'
import DashboardTabs from './DashboardTabs.vue'
import AiChat from './AiChat.vue'

const route = useRoute()

const upcomingEvents = ref([])

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())

const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const monthLabel = computed(() => `${monthNames[currentMonth.value]} ${currentYear.value}`)
const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const daysInMonth = computed(() => new Date(currentYear.value, currentMonth.value + 1, 0).getDate())

const selectedDate = ref(null)

const selectDay = (dayInfo) => {
  if (!dayInfo.day) return
  selectedDate.value = `${currentYear.value}-${String(currentMonth.value + 1).padStart(2, '0')}-${String(dayInfo.day).padStart(2, '0')}`
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value += 1 
  } else {
    currentMonth.value += 1
  }
}

const prevMonth = () => {
    if (currentMonth.value === 0) {
        currentMonth.value = 11
        currentYear.value -= 1
    } else {
        currentMonth.value -= 1
    }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const formatTime = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const calendarDays = computed(() => {
  const firstDayOfMonth = new Date(currentYear.value, currentMonth.value, 1).getDay()
  const emptyDaysCount = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1

  const emptyDays = Array.from({ length: emptyDaysCount }, (_, i) => ({
    day: null,
    hasEvent: false,
    isToday: false
  }))

  const realDays = Array.from({ length: daysInMonth.value }, (_, i) => {
    const day = i + 1
    const dayEvent = upcomingEvents.value.find(e => {
        const eventDate = new Date(e.day)
        return eventDate.getDate() === day && 
                eventDate.getMonth() === currentMonth.value && 
                eventDate.getFullYear() === currentYear.value
    })
    
    return {
      day,
      hasEvent: !!dayEvent,
      isToday: day === new Date().getDate() && 
               currentMonth.value === new Date().getMonth() &&
               currentYear.value === new Date().getFullYear()
    }
  })

  return [...emptyDays, ...realDays]
})

const fetchEvents = async () => {
  try {
    const role = localStorage.getItem('userRole')
    const userId = localStorage.getItem('userId')
    
    if (role === 'student') {
      const coursesRes = await fetch(`http://127.0.0.1:8000/api/courses/student/${userId}`)
      const enrolledCourses = await coursesRes.json()
      const enrolledIds = enrolledCourses.map(c => c.id)
      
      const eventsRes = await fetch('http://127.0.0.1:8000/api/events')
      const allEvents = await eventsRes.json()
      
      upcomingEvents.value = allEvents.filter(e => enrolledIds.includes(e.course_id))
    } else {
      const response = await fetch('http://127.0.0.1:8000/api/events')
      if (response.ok) {
        upcomingEvents.value = await response.json()
      }
    }
  } catch (error) {
    console.error("Failed to fetch events:", error)
  }
}

const filteredEvents = computed(() => {
  if (!selectedDate.value) {
    const today = new Date().toISOString().split('T')[0]
    return upcomingEvents.value.filter(e => e.day === today)
  }
  return upcomingEvents.value.filter(e => e.day === selectedDate.value)
})

onMounted(() => {
  fetchEvents()
})
</script>

<template>
    <DashboardTabs />
    <div class="min-h-screen bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900">Calendar</h1>
                <p class="text-gray-600 mt-2">Manage your schedule and deadlines</p>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-lg shadow p-6">
                        <div class="flex items-center justify-between mb-6">
                            <h2 class="text-xl font-semibold text-gray-900">{{ monthLabel }}</h2>
                            <div class="flex gap-2">
                                <button @click="prevMonth" class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                                    Previous
                                </button>
                                <button @click="nextMonth" class="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 transition-colors">
                                    Next
                                </button>
                            </div>
                        </div>

                        <div class="grid grid-cols-7 gap-2">
                            <div v-for="day in weekDays" :key="day" class="text-center text-sm font-medium text-gray-600 py-2">
                                {{ day }}
                            </div>

                            <div
                                v-for="(dayInfo, index) in calendarDays"
                                @click="selectDay(dayInfo)"
                                :key="index"
                                class="aspect-square p-2 text-center rounded-lg transition-colors"
                                :class="{
                                    'bg-blue-600 text-white font-semibold': dayInfo.isToday && dayInfo.day,
                                    'bg-blue-50 text-gray-900 hover:bg-blue-100': dayInfo.hasEvent && !dayInfo.isToday && dayInfo.day,
                                    'text-gray-700 hover:bg-gray-50': !dayInfo.isToday && !dayInfo.hasEvent && dayInfo.day,
                                    'cursor-default': !dayInfo.day,
                                    'cursor-pointer': dayInfo.day
                                }"
                            >
                                <div class="flex flex-col items-center justify-center h-full">
                                    <span v-if="dayInfo.day">{{ dayInfo.day }}</span>
                                    <div v-if="dayInfo.hasEvent && !dayInfo.isToday && dayInfo.day" class="w-1 h-1 bg-blue-600 rounded-full mt-1"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-1">
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Upcoming Events</h3>
                        <div class="space-y-4">
                            <div
                                v-for="event in filteredEvents"
                                :key="event.id"
                                class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                            >
                                <div class="flex items-start gap-3">
                                    <div :class="['p-2 rounded bg-blue-100 text-blue-600']">
                                        <Video v-if="event.type === 'lecture'" class="w-5 h-5" />
                                        <FileText v-else-if="event.type === 'assignment'" class="w-5 h-5" />
                                        <CheckCircle v-else-if="event.type === 'quiz'" class="w-5 h-5" />
                                        <Calendar v-else class="w-5 h-5" />
                                    </div>
                                    <div class="flex-1">
                                        <h4 class="font-medium text-gray-900 mb-1">{{ event.title }}</h4>
                                        <p class="text-sm text-gray-600 mb-2">{{ event.course || 'General' }}</p>
                                        <div class="flex items-center gap-2 text-sm text-gray-600">
                                            <Calendar class="w-4 h-4" />
                                            <span>{{ formatDate(event.day) }}</span>
                                            <span>•</span>
                                            <Clock class="w-4 h-4" />
                                            <span>{{ formatTime(event.day) }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center gap-4">
                        <div class="bg-blue-100 p-3 rounded-lg">
                            <Video class="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Live Sessions</p>
                            <p class="text-2xl font-bold text-gray-900">3</p>
                            <p class="text-xs text-gray-500">This week</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center gap-4">
                        <div class="bg-orange-100 p-3 rounded-lg">
                            <FileText class="w-6 h-6 text-orange-600" />
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Assignments</p>
                            <p class="text-2xl font-bold text-gray-900">5</p>
                            <p class="text-xs text-gray-500">Due soon</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center gap-4">
                        <div class="bg-green-100 p-3 rounded-lg">
                            <CheckCircle class="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Completed</p>
                            <p class="text-2xl font-bold text-gray-900">12</p>
                            <p class="text-xs text-gray-500">This month</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    <AiChat v-if="route.name && !route.meta.hideNavbar" />
    </div>
</template>