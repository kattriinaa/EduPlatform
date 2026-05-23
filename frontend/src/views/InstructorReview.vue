<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { User, Code, FileText, CheckCircle, AlertCircle, Archive } from 'lucide-vue-next'
import DashboardTabs from './DashboardTabs.vue'
import AiChat from './AiChat.vue'

const route = useRoute()

const submissions = ref([])
const isLoading = ref(true)
const revisionComments = ref({})

const fetchPending = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/instructor/all-submissions')
    if (response.ok) {
      submissions.value = await response.json()
    }
  } catch (err) {
    console.error("Error fetching submissions:", err)
  } finally {
    isLoading.value = false
  }
}

const approveSubmission = async (subId) => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/submissions/${subId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: "approved" })
    });

    if (response.ok) {
      const sub = submissions.value.find(s => (s.id || s._id) === subId)
      if (sub) {
        sub.status = 'approved'
      }
    }
  } catch (err) {
    console.error("Error:", err);
  }
}

const handleNeedsRevision = async (subId) => { 
  const comment = revisionComments.value[subId];
  if (!comment?.trim()) return;

  try {
    const response = await fetch(`http://127.0.0.1:8000/api/assignments/${subId}/revision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        status: 'needs_revision',
        feedback: comment.trim() 
      })
    });

    if (response.ok) {
      const sub = submissions.value.find(s => (s.id || s._id) === subId)
      if (sub) {
        sub.status = 'needs_revision';
      }
    }
  } catch (err) {
    console.error("Error:", err);
  }
}

const pendingSubmissions = computed(() => 
  submissions.value.filter(s => s.status === 'pending')
)

const archiveSubmissions = computed(() => 
  submissions.value.filter(s => s.status === 'approved' || s.status === 'needs_revision')
)

onMounted(fetchPending)
</script>

<template>
    <DashboardTabs />
    <div class="max-w-6xl mx-auto p-8">
        <header class="mb-10">
        <h1 class="text-3xl font-bold text-gray-900">Review Assignments</h1>
        <p class="text-gray-500">Review student submissions and provide feedback.</p>
        </header>

        <div v-if="isLoading" class="flex justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <div v-else class="space-y-12">
        
        <section>
            <h2 class="text-xl font-bold mb-6 flex items-center gap-2 text-gray-800">
            <span class="w-2 h-2 bg-orange-500 rounded-full animate-ping"></span>
            Pending Submissions ({{ pendingSubmissions.length }})
            </h2>

            <div v-if="pendingSubmissions.length === 0" class="text-center py-16 bg-gray-50 rounded-3xl border-2 border-dashed border-gray-200">
            <div class="inline-flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-sm mb-4">
                <CheckCircle class="text-green-500 w-6 h-6" />
            </div>
            <p class="text-gray-500">No pending assignments to review. Great job!</p>
            </div>

            <div v-else class="grid gap-8">
            <div v-for="sub in pendingSubmissions" :key="sub.id || sub._id" class="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all">
                
                <div class="p-6 border-b border-gray-50 bg-gray-50/50 flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                    {{ sub.student_name?.charAt(0) }}
                    </div>
                    <div>
                    <h3 class="font-bold text-gray-900">{{ sub.student_name }}</h3>
                    <p class="text-xs text-gray-400 font-semibold uppercase tracking-wider">Lesson: {{ sub.lesson_title }}</p>
                    </div>
                </div>
                </div>

                <div v-if="sub.assignment_instruction" class="px-6 py-4 bg-amber-50/50 border-b border-amber-100">
                <div class="flex items-center gap-2 text-[10px] font-black text-amber-600 uppercase tracking-widest mb-1">
                    <FileText class="w-3.5 h-3.5" /> Assignment Instructions
                </div>
                <p class="text-gray-700 text-sm leading-relaxed">{{ sub.assignment_instruction }}</p>
                </div>

                <div class="p-6">
                <div class="flex items-center gap-2 text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">
                    <Code class="w-4 h-4" /> Student's Response
                </div>
                <div class="bg-gray-900 text-green-400 p-5 rounded-xl font-mono text-sm border border-gray-800 shadow-inner">
                    <pre class="whitespace-pre-wrap">{{ sub.answer }}</pre>
                </div>
                </div>

                <div class="px-6 pb-6">
                <label class="block text-[10px] font-black text-gray-400 mb-2 uppercase tracking-widest">
                    Your Feedback:
                </label>
                <textarea 
                    v-model="revisionComments[sub.id || sub._id]" 
                    rows="3" 
                    class="w-full p-4 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 outline-none bg-gray-50 transition-all"
                    placeholder="Explain what needs to be fixed..."
                ></textarea>
                </div>

                <div class="p-5 bg-gray-50/30 border-t border-gray-100 flex gap-4">
                <button 
                    @click="approveSubmission(sub.id || sub._id)"
                    class="flex-1 bg-green-600 text-white py-3 rounded-xl font-bold hover:bg-green-700 active:scale-95 transition-all shadow-sm"
                >
                    Approve
                </button>
                <button 
                    @click="handleNeedsRevision(sub.id || sub._id)" 
                    :disabled="!revisionComments[sub.id || sub._id]?.trim()"
                    class="flex-1 bg-orange-500 text-white py-3 rounded-xl font-bold hover:bg-orange-600 active:scale-95 transition-all disabled:opacity-50 shadow-sm"
                >
                    Needs Revision
                </button>
                </div>
            </div>
            </div>
        </section>

        <section v-if="archiveSubmissions.length > 0">
            <h2 class="text-xl font-bold mb-6 flex items-center gap-2 text-gray-400">
            <Archive class="w-5 h-5" /> Archive & History
            </h2>
            
            <div class="overflow-hidden bg-white border border-gray-200 rounded-2xl shadow-sm">
            <table class="w-full text-left text-sm">
                <thead class="bg-gray-50 border-b border-gray-200 text-gray-500 text-[10px] font-black uppercase tracking-widest">
                <tr>
                    <th class="px-6 py-4">Student</th>
                    <th class="px-6 py-4">Lesson</th>
                    <th class="px-6 py-4">Status</th>
                    <th class="px-6 py-4 text-right">Result</th>
                </tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                <tr v-for="sub in archiveSubmissions" :key="sub.id || sub._id" class="hover:bg-gray-50/50 transition-colors">
                    <td class="px-6 py-4 font-bold text-gray-900">{{ sub.student_name }}</td>
                    <td class="px-6 py-4 text-gray-500">{{ sub.lesson_title }}</td>
                    <td class="px-6 py-4">
                    <span :class="{
                        'bg-green-100 text-green-700': sub.status === 'approved',
                        'bg-orange-100 text-orange-700': sub.status === 'needs_revision'
                    }" class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter">
                        {{ sub.status }}
                    </span>
                    </td>
                    <td class="px-6 py-4 text-right text-xs text-gray-400 font-mono">
                    DONE
                    </td>
                </tr>
                </tbody>
            </table>
            </div>
        </section>

        </div>
    <AiChat v-if="route.name && !route.meta.hideNavbar" />
    </div>
</template>