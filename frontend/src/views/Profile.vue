<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { 
  User, LogOut, Mail, ShieldCheck, ArrowLeft, 
  BookOpen, Users, Award, TrendingUp, RotateCcw, CheckCircle
} from 'lucide-vue-next'

import { Doughnut } from 'vue-chartjs'
import { 
  Chart as ChartJS, 
  Title, Tooltip, Legend, ArcElement, CategoryScale 
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, ArcElement, CategoryScale)

const router = useRouter()
const route = useRoute()

const userName = computed(() => localStorage.getItem('userName') || 'User')
const userId = localStorage.getItem('userId')
const userRole = computed(() => localStorage.getItem('userRole') || 'student')
const userEmail = ref('')

const stats = ref({
  activeCourses: 0,
  completedLessons: 0,
  avgProgress: 0
})
const teacherCourses = ref([])
const pendingSubmissions = ref(0)
const teacherStats = ref({ approved: 0, needsRevision: 0 }) 

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  cutout: '75%'
}

const studentChartData = computed(() => ({
  labels: ['Completed', 'Remaining'],
  datasets: [{
    backgroundColor: ['#6366f1', '#f1f5f9'],
    borderWidth: 0,
    data: [stats.value.avgProgress, 100 - stats.value.avgProgress]
  }]
}))

const teacherChartData = computed(() => ({
  labels: ['Approved', 'Needs Revision', 'Pending'],
  datasets: [{
    backgroundColor: ['#10b981', '#f43f5e', '#f59e0b'],
    borderWidth: 0,
    data: [
      teacherStats.value.approved, 
      teacherStats.value.needsRevision, 
      pendingSubmissions.value
    ]
  }]
}))

const teacherWorkloadHours = computed(() => {
  const totalMinutes = teacherCourses.value.reduce((sum, c) => 
    sum + (c.modules?.flatMap(m => m.lessons || [])
      .reduce((s, l) => s + (parseInt(l.duration) || 0), 0) || 0), 0)
  return Math.round(totalMinutes / 60)
})

const fetchStats = async () => {
  if (!userId) return;
  try {
    const userRes = await fetch(`http://127.0.0.1:8000/api/users/${userId}`)
    const userData = await userRes.json()
    userEmail.value = userData.email || ''

    if (userRole.value === 'student') {
      const coursesRes = await fetch(`http://127.0.0.1:8000/api/courses/student/${userId}`)
      const courses = await coursesRes.json()
      const totalLessons = courses.flatMap(c => c.modules?.flatMap(m => m.lessons || []) || []).length
      const completed = userData.completed_lessons?.length || 0
      stats.value = {
        activeCourses: courses.length,
        completedLessons: completed,
        avgProgress: totalLessons > 0 ? Math.round((completed / totalLessons) * 100) : 0
      }
    } else {
      const coursesRes = await fetch(`http://127.0.0.1:8000/api/courses/teacher/${userId}`)
      const courses = await coursesRes.json()
      teacherCourses.value = courses
      stats.value = {
        activeCourses: courses.length,
        completedLessons: courses.reduce((sum, c) => sum + (c.students || 0), 0),
        avgProgress: 0
      }
    }
  } catch (e) { console.error(e) }
}

const fetchTeacherReport = async () => {
  if (userRole.value !== 'teacher' || !userId) return
  
  try {
    const statsRes = await fetch(`http://127.0.0.1:8000/api/submissions/teacher/${userId}/stats`)
    
    if (statsRes.ok) {
      const data = await statsRes.json()
      
      teacherStats.value = {
        approved: data.approved || 0,
        needsRevision: data.needs_revision || 0
      }
      pendingSubmissions.value = data.pending || 0
    }
    
    const coursesRes = await fetch(`http://127.0.0.1:8000/api/courses/teacher/${userId}`)
    if (coursesRes.ok) {
      teacherCourses.value = await coursesRes.json()
    }

  } catch (e) {
    console.error("Teacher report error:", e)
  }
}

onMounted(async () => {
  await fetchStats()
  await fetchTeacherReport()
})

const logout = () => { localStorage.clear(); router.push('/login'); }
</script>

<template>
  <div class="min-h-screen bg-[#F8FAFC] p-6 md:p-12 font-sans text-slate-700">
    <div class="max-w-3xl mx-auto">
      
      <button @click="router.back()" class="flex items-center gap-2 text-slate-400 hover:text-indigo-600 transition-colors mb-8 group">
        <ArrowLeft class="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
        <span class="text-sm font-medium">Back</span>
      </button>

      <div class="bg-white rounded-[2.5rem] shadow-sm border border-slate-100 overflow-hidden">
        <div class="h-32 bg-gradient-to-r from-indigo-600 to-violet-600"></div>

        <div class="px-8 pb-8">
          <div class="relative flex justify-between items-end -mt-12 mb-8">
            <div class="w-24 h-24 bg-white rounded-3xl p-1 shadow-xl">
              <div class="w-full h-full bg-slate-100 rounded-[1.25rem] flex items-center justify-center">
                <User class="w-12 h-12 text-slate-300" />
              </div>
            </div>
          </div>

          <div class="mb-10">
            <h1 class="text-3xl font-bold text-slate-900 leading-tight">{{ userName }}</h1>
            <div class="flex items-center gap-2 mt-1 text-slate-400">
              <ShieldCheck class="w-4 h-4 text-emerald-500" />
              <span class="text-sm font-semibold uppercase tracking-wider">{{ userRole }} Account</span>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
            <div class="bg-slate-50 border border-slate-100 rounded-[2rem] p-6 flex flex-col items-center justify-center min-h-[240px]">
              <h3 class="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-4">
                {{ userRole === 'teacher' ? 'Review Distribution' : 'Performance Overview' }}
              </h3>
              <div class="w-full h-32 relative">
                <Doughnut :data="userRole === 'teacher' ? teacherChartData : studentChartData" :options="chartOptions" />
                <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                  <span class="text-2xl font-black text-slate-800">
                    {{ userRole === 'teacher' ? (teacherStats.approved + teacherStats.needsRevision + pendingSubmissions) : stats.avgProgress + '%' }}
                  </span>
                  <span class="text-[9px] font-bold text-slate-400 uppercase">
                    {{ userRole === 'teacher' ? 'Total tasks' : 'Progress' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="bg-indigo-600 rounded-[2.5rem] p-8 text-white relative overflow-hidden flex flex-col justify-between">
              <div class="relative z-10">
                <p class="text-indigo-100 text-[10px] font-bold uppercase tracking-widest mb-2">Current Status</p>
                <h4 class="text-xl font-medium leading-snug">
                  {{ userRole === 'teacher' ? 'Your courses are growing! You have ' + stats.completedLessons + ' students.' : 'You have completed ' + stats.completedLessons + ' lessons this term!' }}
                </h4>
              </div>
              <Award class="absolute -right-4 -bottom-4 w-32 h-32 text-white/10" />
              <div class="relative z-10 text-xs font-bold bg-white/20 self-start px-4 py-2 rounded-full backdrop-blur-md">
                Keep it up! ✨
              </div>
            </div>
          </div>

          <div v-if="userRole === 'teacher'" class="mb-10 space-y-4">
            <h2 class="text-sm font-bold text-slate-400 uppercase tracking-widest px-2">📊 Teacher Report</h2>
            
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div class="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 flex flex-col gap-1">
                <div class="flex items-center gap-2 text-emerald-600">
                  <CheckCircle class="w-4 h-4" />
                  <span class="text-[10px] font-bold uppercase tracking-wider">Approved</span>
                </div>
                <span class="text-2xl font-black text-emerald-700">{{ teacherStats.approved }}</span>
              </div>
              
              <div class="p-4 rounded-2xl bg-rose-50 border border-rose-100 flex flex-col gap-1">
                <div class="flex items-center gap-2 text-rose-600">
                  <RotateCcw class="w-4 h-4" />
                  <span class="text-[10px] font-bold uppercase tracking-wider">Resubmit</span>
                </div>
                <span class="text-2xl font-black text-rose-700">{{ teacherStats.needsRevision }}</span>
              </div>

              <div class="p-4 rounded-2xl bg-amber-50 border border-amber-100 flex flex-col gap-1">
                <div class="flex items-center gap-2 text-amber-600">
                  <TrendingUp class="w-4 h-4" />
                  <span class="text-[10px] font-bold uppercase tracking-wider">Pending</span>
                </div>
                <span class="text-2xl font-black text-amber-700">{{ pendingSubmissions }}</span>
              </div>
            </div>

            <div class="p-5 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <Users class="w-5 h-5 text-blue-500" />
                <span class="text-sm font-bold text-slate-700">Total Teaching Workload</span>
              </div>
              <span class="text-xl font-black text-blue-600">{{ teacherWorkloadHours }} hrs</span>
            </div>
            
            <div class="space-y-2">
              <div v-for="course in teacherCourses" :key="course.id" class="p-4 bg-white border border-slate-100 rounded-2xl flex items-center justify-between hover:border-indigo-200 transition-colors">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center text-indigo-600 font-bold text-xs uppercase">
                    {{ course.title.substring(0, 2) }}
                  </div>
                  <div>
                    <p class="text-sm font-bold text-slate-800">{{ course.title }}</p>
                    <p class="text-[10px] text-slate-400 font-medium tracking-wide uppercase">{{ course.students || 0 }} Students Enrolled</p>
                  </div>
                </div>
                <BookOpen class="w-4 h-4 text-slate-200" />
              </div>
            </div>
          </div>

          <div v-if="userRole !== 'teacher'" class="grid grid-cols-2 gap-4 mb-10">
            <div class="p-6 bg-slate-50 rounded-[2rem] text-center border border-slate-100">
              <p class="text-3xl font-black text-indigo-600">{{ stats.activeCourses }}</p>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Active Courses</p>
            </div>
            <div class="p-6 bg-slate-50 rounded-[2rem] text-center border border-slate-100">
              <p class="text-3xl font-black text-emerald-600">{{ stats.completedLessons }}</p>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Lessons Done</p>
            </div>
          </div>

          <div class="p-5 bg-slate-50 rounded-2xl border border-slate-100 flex items-center gap-4 mb-10">
            <div class="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm">
              <Mail class="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Registered Email</p>
              <p class="text-sm font-bold text-slate-700">{{ userEmail || 'Loading...' }}</p>
            </div>
          </div>

          <button @click="logout" class="w-full flex items-center justify-center gap-3 px-6 py-5 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-[1.5rem] font-black transition-all duration-300 group">
            <LogOut class="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            LOG OUT
          </button>
        </div>
      </div>
    </div>
  </div>
</template>