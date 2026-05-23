<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { 
  FileText, CheckCircle2, Search, 
  ChevronRight, Loader2, MessageSquare, AlertCircle, Calendar
} from 'lucide-vue-next';
import DashboardTabs from './DashboardTabs.vue'
import AiChat from './AiChat.vue'

const router = useRouter();
const assignments = ref([]);
const isLoading = ref(true);
const searchQuery = ref('');
const activeFilter = ref('all');

const isDueThisWeek = (dateStr) => {
  if (!dateStr) return false;
  const now = new Date();
  const due = new Date(dateStr);
  const diffTime = due - now;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays >= 0 && diffDays <= 7;
};

const filteredTasks = computed(() => {
  let tasks = assignments.value.filter(task => 
    task.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    task.courseName.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
  
  if (activeFilter.value !== 'all') {
    tasks = tasks.filter(t => t.status === activeFilter.value)
  }
  
  return tasks.sort((a, b) => {
    if (!a.dueDate) return 1
    if (!b.dueDate) return -1
    return new Date(a.dueDate) - new Date(b.dueDate)
  })
})

const criticalStats = computed(() => {
  return {
    needsRevision: assignments.value.filter(t => t.status === 'needs_revision').length,
    dueSoon: assignments.value.filter(t => t.status === 'pending_submission' && isDueThisWeek(t.dueDate)).length
  }
})

const fetchAssignments = async () => {
  try {
    isLoading.value = TreeNodeValueGroup
    const headers = { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' };

    const userId = localStorage.getItem('userId');
    
    if (!userId) {
      console.error("User ID is not found in localStorage");
      isLoading.value = false;
      return;
    }
    
    const [coursesRes, eventsRes] = await Promise.all([
      fetch(`http://127.0.0.1:8000/api/courses/student/${userId}`, { headers }),
      fetch('http://127.0.0.1:8000/api/events', { headers })
    ]);

    const enrolledCourses = await coursesRes.json();
    const events = await eventsRes.json();

    const rawTasks = [];

    enrolledCourses.forEach(course => {
      course.modules?.forEach(module => {
        module.lessons?.forEach(lesson => {
          if (lesson.type === 'assignment') {
            const taskEvent = events.find(e =>
              Number(e.course_id) === Number(course.id) &&
              e.title.trim().toLowerCase() === lesson.title.trim().toLowerCase()
            );
            rawTasks.push({ lesson, course, taskEvent });
          }
        })
      })
    })

    const results = await Promise.all(rawTasks.map(async ({ lesson, course, taskEvent }) => {
      let status = 'pending_submission';
      let teacherComment = null;

      try {
        const subRes = await fetch(
          `http://127.0.0.1:8000/api/submissions/status?user_id=${userId}&lesson_id=${lesson.id}`, 
          { headers }
        );
        if (subRes.ok) {
          const subData = await subRes.json();
          if (subData.status) status = subData.status;
          teacherComment = subData.feedback || null;
        }
      } catch (e) {
        console.warn(`Could not fetch status for lesson ${lesson.id}`);
      }

      return {
        id: lesson.id,
        courseId: course.id,
        title: lesson.title,
        courseName: course.title,
        status,
        teacherComment,
        dueDate: taskEvent ? taskEvent.day : null
      };
    }));

    assignments.value = results;
  } catch (error) {
    console.error("Failed to fetch assignments:", error);
  } finally {
    isLoading.value = false;
  }
}

onMounted(fetchAssignments);

const statusConfig = {
  'needs_revision': { color: 'text-rose-600 bg-rose-50', icon: AlertCircle, label: 'Revision Required' },
  'approved': { color: 'text-emerald-600 bg-emerald-50', icon: CheckCircle2, label: 'Completed' },
  'pending_submission': { color: 'text-slate-400 bg-slate-50', icon: FileText, label: 'Pending' },
  'submitted': { color: 'text-blue-600 bg-blue-50', icon: Loader2, label: 'In Review' }
};

const goToLesson = (courseId, lessonId) => {
  if (courseId && lessonId) router.push(`/course/${courseId}/lesson/${lessonId}`);
};
</script>

<template>
  <DashboardTabs />
  <div class="min-h-screen bg-[#FBFBFE] p-6 md:p-12 font-sans text-slate-700">
    <div class="max-w-4xl mx-auto">
      
      <header class="mb-12">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Assignments</h1>
            <p class="text-slate-400 mt-1 text-sm">Monitor your tasks and performance</p>
          </div>

          <div class="flex gap-3">
             <div v-if="criticalStats.needsRevision > 0" 
                  class="flex items-center gap-2 px-4 py-2 bg-rose-50 border border-rose-100 rounded-2xl animate-pulse">
                <AlertCircle class="w-4 h-4 text-rose-500" />
                <span class="text-xs font-bold text-rose-600">{{ criticalStats.needsRevision }} Tasks to Fix</span>
             </div>
             <div v-if="criticalStats.dueSoon > 0" 
                  class="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-100 rounded-2xl">
                <Calendar class="w-4 h-4 text-amber-500" />
                <span class="text-xs font-bold text-amber-600">{{ criticalStats.dueSoon }} Due This Week</span>
             </div>
          </div>
        </div>

        <div class="mt-10 flex flex-col md:flex-row gap-4 items-center">
          <div class="relative w-full md:w-auto flex-grow group">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300 group-focus-within:text-indigo-500" />
            <input v-model="searchQuery" type="text" placeholder="Search assignments..." 
                   class="pl-11 pr-6 py-3.5 bg-white border border-slate-100 rounded-2xl text-sm w-full outline-none focus:border-indigo-200 focus:ring-4 focus:ring-indigo-500/5 transition-all shadow-sm" />
          </div>
          <div class="flex gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0">
            <button v-for="opt in [
              { key: 'all', label: 'All' },
              { key: 'needs_revision', label: 'Fixes' },
              { key: 'approved', label: 'Done' },
              { key: 'pending_submission', label: 'To-Do' }
            ]" :key="opt.key" @click="activeFilter = opt.key"
              class="px-5 py-3 rounded-2xl text-xs font-bold whitespace-nowrap transition-all border"
              :class="activeFilter === opt.key ? 'bg-indigo-600 text-white border-indigo-600 shadow-lg shadow-indigo-200' : 'bg-white text-slate-400 border-slate-100 hover:border-indigo-100'">
              {{ opt.label }}
            </button>
          </div>
        </div>
      </header>

      <div v-if="!isLoading" class="space-y-6">
        <div v-for="task in filteredTasks" :key="task.id"
          class="relative bg-white border border-slate-100 rounded-[2.5rem] p-6 md:p-8 transition-all hover:shadow-2xl hover:shadow-indigo-500/10 group overflow-hidden"
          :class="{ 
            'border-rose-200 bg-rose-50/20': task.status === 'needs_revision',
            'border-amber-200 bg-amber-50/20': isDueThisWeek(task.dueDate) && task.status === 'pending_submission'
          }">
          
          <div v-if="task.status === 'needs_revision'" class="absolute left-0 top-0 bottom-0 w-1.5 bg-rose-500"></div>
          <div v-else-if="isDueThisWeek(task.dueDate) && task.status === 'pending_submission'" class="absolute left-0 top-0 bottom-0 w-1.5 bg-amber-500"></div>

          <div class="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div class="flex items-start gap-5">
              <div :class="['w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm', 
                           task.status === 'needs_revision' ? 'bg-white text-rose-500 border border-rose-100' : 'bg-indigo-50 text-indigo-500']">
                <FileText class="w-6 h-6" />
              </div>

              <div>
                <div class="flex flex-wrap items-center gap-3 mb-1">
                  <h3 class="text-lg font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">{{ task.title }}</h3>
                  <span v-if="isDueThisWeek(task.dueDate) && task.status === 'pending_submission'" 
                        class="px-2 py-0.5 rounded-lg bg-amber-500 text-[9px] font-black uppercase text-white">Due Soon</span>
                </div>
                
                <div class="flex items-center gap-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {{ task.courseName }}
                  <span v-if="task.dueDate" class="flex items-center gap-1.5 normal-case tracking-normal text-slate-300">
                    <span class="w-1 h-1 rounded-full bg-slate-200"></span>
                    Deadline: {{ new Date(task.dueDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="statusConfig[task.status]" 
              :class="['px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2 self-start md:self-center shadow-sm', statusConfig[task.status].color]">
              <component :is="statusConfig[task.status].icon" class="w-3.5 h-3.5" />
              {{ statusConfig[task.status].label }}
            </div>
          </div>

          <div v-if="task.teacherComment" 
            class="mt-6 p-5 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-inner flex gap-4">
            <div class="w-8 h-8 bg-indigo-50 rounded-full flex items-center justify-center flex-shrink-0">
              <MessageSquare class="w-4 h-4 text-indigo-500" />
            </div>
            <div>
              <p class="text-[9px] font-black uppercase tracking-[0.15em] text-indigo-400 mb-1">Instructor's Note</p>
              <p class="text-sm text-slate-600 leading-relaxed italic font-medium">"{{ task.teacherComment }}"</p>
            </div>
          </div>

          <div class="mt-8 flex items-center justify-between pt-6 border-t border-slate-100/50">
            <div class="flex items-center gap-2 text-[11px] font-bold text-slate-300">
              <span class="w-2 h-2 rounded-full" :class="task.status === 'approved' ? 'bg-emerald-400' : 'bg-slate-200'"></span>
              {{ task.status === 'approved' ? 'Ready to move forward' : 'Action required' }}
            </div>
            
            <button @click="goToLesson(task.courseId, task.id)"
              class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-indigo-600 hover:shadow-lg hover:shadow-indigo-200 transition-all active:scale-95">
              {{ task.status === 'needs_revision' ? 'Edit Submission' : 'View Materials' }}
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div v-if="filteredTasks.length === 0" class="text-center py-20 bg-white rounded-[3rem] border-2 border-dashed border-slate-50">
          <div class="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Search class="w-8 h-8 text-slate-200" />
          </div>
          <h4 class="text-slate-900 font-bold">No assignments matches</h4>
          <p class="text-slate-400 text-sm mt-1">Try adjusting your filters or search query</p>
        </div>
      </div>

      <div v-else class="py-32 flex flex-col items-center justify-center">
        <div class="relative">
          <Loader2 class="w-12 h-12 animate-spin text-indigo-500 mb-4" />
          <div class="absolute inset-0 blur-xl bg-indigo-400/20 animate-pulse"></div>
        </div>
        <p class="text-slate-400 text-sm font-bold tracking-widest uppercase">Syncing with database</p>
      </div>

    </div>
    <AiChat />
  </div>
</template>

<style scoped>
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .7; }
}
</style>