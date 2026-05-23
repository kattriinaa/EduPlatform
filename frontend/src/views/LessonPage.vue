<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, ChevronRight, CheckCircle, AlertCircle, RefreshCw, FileText } from 'lucide-vue-next'
import AiChat from './AiChat.vue'

const route = useRoute()
const router = useRouter()

const courseId = route.params.courseId 
const lessonId = route.params.lessonId
const userId = localStorage.getItem('userId')
const userRole = localStorage.getItem('userRole')

const lesson = ref(null)
const isLoading = ref(true)
const completedLessons = ref([])

const selectedAnswers = ref({})
const testResult = ref(null)
const score = ref(0)

const assignmentAnswer = ref('')
const isSubmitting = ref(false)
const showSuccessAlert = ref(false)
const errorMessage = ref('')
const submissionStatus = ref(null)

const teacherFeedback = ref('')

const props = defineProps({
  courseId: String,
  lessonId: String
})

const showAlert = () => {
  showSuccessAlert.value = true
  setTimeout(() => {
    showSuccessAlert.value = false
  }, 3000)
}

const fetchLesson = async () => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/courses/${courseId}/lessons/${lessonId}`)
    if (response.ok) {
      lesson.value = await response.json()
    }
  } catch (err) {
    console.error("Failed to fetch lesson:", err)
  }
}

const fetchUserProgress = async () => {
  if (!userId) return
  try {
    const headers = { 'Cache-Control': 'no-cache' }; 
    const response = await fetch(`http://127.0.0.1:8000/api/users/${userId}`, { headers })
    
    if (response.ok) {
      const data = await response.json()
      completedLessons.value = data.completed_lessons || []
    }
    
    if (lesson.value?.type === 'assignment') {
      const resSub = await fetch(`http://127.0.0.1:8000/api/submissions/status?user_id=${userId}&lesson_id=${lessonId}`, { headers })
      if (resSub.ok) {
        const subData = await resSub.json()
        submissionStatus.value = subData.status
        teacherFeedback.value = subData.feedback || ''
        
        if (subData.status === 'approved' && !isCompleted.value) {
           completedLessons.value.push(`${courseId}_${lessonId}`)
        }
      }
    }
  } catch (error) {
    console.error("Error fetching progress:", error)
  }
}

const isCompleted = computed(() => {
  return completedLessons.value.includes(`${courseId}_${lessonId}`)
})

const checkQuiz = async () => {
  let correctCount = 0
  lesson.value.quiz.questions.forEach((q, index) => {
    if (selectedAnswers.value[index] === q.correctAnswer) correctCount++
  })
  score.value = Math.round((correctCount / lesson.value.quiz.questions.length) * 100)
  await submitQuizResults(score.value)
  if (score.value >= 80) {
    testResult.value = 'passed'
    completeLesson()
  } else {
    testResult.value = 'failed'
  }
}

const resetQuiz = () => {
  selectedAnswers.value = {}
  testResult.value = null
  score.value = 0
}

const completeLesson = async () => {
  if (!userId) return
  try {
    const response = await fetch('http://127.0.0.1:8000/api/lessons/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: parseInt(userId),
        lesson_id: `${courseId}_${lessonId}`
      })
    })
    if (response.ok) {
      await fetchUserProgress()
    }
  } catch (err) {
    console.error("Error saving progress:", err)
  }
}

const submitQuizResults = async (score) => {
  try {
    await fetch('http://127.0.0.1:8000/api/lessons/quiz-attempt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: parseInt(userId),
        lesson_id: `${courseId}_${lessonId}`,
        score: score,
        answers: selectedAnswers.value,
        is_passed: score >= 80
      })
    })
  } catch (err) {
    console.error("Failed to save quiz attempt:", err)
  }
}

const submitAssignment = async () => {
  if (!assignmentAnswer.value.trim()) return;
  const sName = localStorage.getItem('userName') || 'Student';
  const uId = localStorage.getItem('userId');
  isSubmitting.value = true;
  
  const payload = {
    user_id: parseInt(uId),
    student_name: String(sName),
    course_id: parseInt(courseId),
    lesson_id: parseInt(lessonId),
    lesson_title: String(lesson.value.title),
    answer: String(assignmentAnswer.value),
    status: 'pending' 
  };

  try {
    const response = await fetch('http://127.0.0.1:8000/api/assignments/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (response.ok) {
      showAlert();
      submissionStatus.value = 'pending';
      teacherFeedback.value = ''; 
    }
  } catch (err) {
    console.error("Submission error:", err)
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(async () => {
  await fetchLesson()
  await fetchUserProgress()
  isLoading.value = false
})
</script>

<template>
  <div>
    <Transition name="fade">
      <div v-if="showSuccessAlert" class="fixed top-10 right-10 z-50 bg-green-600 text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3">
        <CheckCircle class="w-6 h-6" />
        <span class="font-bold">Assignment submitted successfully!</span>
      </div>
    </Transition>

    <div v-if="!isLoading && lesson" class="max-w-5xl mx-auto p-6">
      <button @click="$router.back()" class="flex items-center text-gray-600 mb-6 hover:text-black transition-colors">
        <ChevronLeft class="w-5 h-5" /> Back to Course
      </button>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2">
          <h1 class="text-4xl font-extrabold mb-6 text-gray-900">{{ lesson.title }}</h1>
          
          <div v-if="lesson.videoUrl" class="mb-8">
            <div class="aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl mb-4">
              <iframe class="w-full h-full" :src="lesson.videoUrl" frameborder="0" allowfullscreen></iframe>
            </div>
            <p v-if="lesson.videoDescription" class="text-gray-500 italic text-sm px-2">
              {{ lesson.videoDescription }}
            </p>
          </div>

          <div class="prose max-w-none text-gray-700 leading-relaxed text-lg mb-12 bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
            {{ lesson.content }}
          </div>

          <div v-if="lesson?.type === 'assignment'" class="mt-12 p-8 bg-white border border-gray-200 rounded-3xl shadow-sm">
            <h2 class="text-2xl font-bold mb-4 flex items-center gap-2 text-purple-600">
              <FileText class="w-6 h-6" /> Practical Assignment
            </h2>

            <div v-if="!submissionStatus || submissionStatus === 'needs_revision'">
              
              <div v-if="submissionStatus === 'needs_revision'" class="mb-6 p-6 bg-orange-50 border-2 border-orange-200 rounded-2xl">
                <h3 class="text-orange-800 font-bold flex items-center gap-2 mb-2">
                  <AlertCircle class="w-5 h-5" /> Teacher's Feedback:
                </h3>
                <p class="text-orange-700 italic font-medium">"{{ teacherFeedback }}"</p>
                <p class="mt-4 text-sm text-orange-600">Please review the comments above, update your answer, and resubmit.</p>
              </div>

              <p v-else class="text-gray-600 mb-6 bg-purple-50 p-4 rounded-xl border border-purple-100">
                {{ lesson.assignment_instruction }}
              </p>

              <textarea 
                v-model="assignmentAnswer" 
                rows="8" 
                class="w-full p-4 font-mono text-sm bg-gray-900 text-green-400 rounded-xl border-2 border-gray-800 focus:border-purple-500 focus:outline-none transition-all" 
                placeholder="Type your solution here..."
              ></textarea>

              <button 
                @click="submitAssignment" 
                :disabled="isSubmitting || !assignmentAnswer.trim()" 
                class="mt-6 w-full py-4 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 transition-all shadow-lg"
              >
                {{ isSubmitting ? 'Submitting...' : (submissionStatus === 'needs_revision' ? 'Resubmit Assignment' : 'Submit Assignment') }}
              </button>
            </div>

            <div v-else-if="submissionStatus === 'pending'" class="text-center py-10 bg-blue-50 rounded-3xl border border-blue-100">
              <RefreshCw class="w-12 h-12 text-blue-600 animate-spin-slow mx-auto mb-4" />
              <h3 class="text-xl font-bold text-blue-900">Awaiting Teacher's Review</h3>
              <p class="text-blue-700 mt-2">Your work has been submitted successfully and is waiting for evaluation.</p>
            </div>

            <div v-else-if="submissionStatus === 'approved' || isCompleted" class="text-center py-10 bg-green-50 rounded-3xl border border-green-100">
              <CheckCircle class="w-12 h-12 text-green-600 mx-auto mb-4" />
              <h3 class="text-xl font-bold text-green-900">Task Completed & Approved!</h3>
              <p class="text-green-700 mt-2">Excellent! Your solution has been reviewed and accepted by the instructor.</p>
              
              <div v-if="teacherFeedback && submissionStatus === 'approved'" class="mt-4 p-4 bg-white/50 rounded-xl italic text-sm text-green-800">
                "{{ teacherFeedback }}"
              </div>
            </div>
          </div>
          <div v-if="lesson.quiz" class="mt-12 p-8 bg-white border border-gray-200 rounded-3xl shadow-sm">
            <h2 class="text-2xl font-bold mb-6 flex items-center gap-2">
              <CheckCircle class="text-blue-600" /> Knowledge Check
            </h2>

            <div v-if="isCompleted && testResult !== 'retaking'" class="text-center py-6 bg-green-50 rounded-2xl border border-green-100">
              <div class="flex items-center justify-center gap-3 text-green-700 font-bold text-xl mb-2">
                <CheckCircle class="w-6 h-6" />
                <span>Quiz Already Passed</span>
              </div>
              <button @click="testResult = 'retaking'" class="text-sm font-medium text-gray-500 hover:text-blue-600 flex items-center gap-2 mx-auto transition-colors">
                <RefreshCw class="w-4 h-4" /> Retake Quiz
              </button>
            </div>

            <div v-else>
              <div v-if="testResult !== 'passed'">
                <div v-for="(q, qIdx) in lesson.quiz.questions" :key="qIdx" class="mb-8 p-4 rounded-xl bg-gray-50">
                  <p class="font-semibold text-lg mb-4">{{ qIdx + 1 }}. {{ q.question }}</p>
                  <div class="space-y-3">
                    <label v-for="(opt, optIdx) in q.options" :key="optIdx" class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-blue-50 transition-colors" :class="{'border-blue-500 bg-blue-50': selectedAnswers[qIdx] === optIdx}">
                      <input type="radio" :name="'q'+qIdx" :value="optIdx" v-model="selectedAnswers[qIdx]" class="hidden" />
                      <span class="w-6 h-6 border-2 rounded-full mr-3 flex items-center justify-center" :class="selectedAnswers[qIdx] === optIdx ? 'border-blue-600 bg-blue-600' : 'border-gray-300'">
                        <span v-if="selectedAnswers[qIdx] === optIdx" class="w-2 h-2 bg-white rounded-full"></span>
                      </span>
                      {{ opt }}
                    </label>
                  </div>
                </div>

                <div v-if="testResult === 'failed'" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                  <p class="font-bold">Score: {{ score }}%</p>
                  <button @click="resetQuiz" class="mt-2 flex items-center gap-2 text-sm font-bold text-red-800">
                    <RefreshCw class="w-4 h-4" /> Try Again
                  </button>
                </div>

                <button @click="checkQuiz" :disabled="Object.keys(selectedAnswers).length < lesson.quiz.questions.length" class="w-full py-4 bg-gray-900 text-white rounded-xl font-bold hover:bg-black disabled:opacity-50 transition-all">
                  Submit Answers
                </button>
              </div>

              <div v-else class="text-center py-8">
                <CheckCircle class="w-10 h-10 text-green-600 mx-auto mb-4" />
                <h3 class="text-2xl font-bold text-green-700">Congratulations! {{ score }}%</h3>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-gray-50 p-6 rounded-2xl border border-gray-100 sticky top-6">
            <h3 class="font-bold text-gray-400 uppercase text-xs tracking-widest mb-4">Lesson Progress</h3>
            <div v-if="userRole !== 'teacher'">
              <div v-if="isCompleted" class="space-y-4">
                <div class="flex items-center gap-2 text-green-700 font-bold bg-green-100 px-4 py-3 rounded-xl border border-green-200">
                  <CheckCircle class="w-6 h-6" />
                  <span>Completed</span>
                </div>
              </div>
              <div v-else-if="!lesson.quiz && lesson.type !== 'assignment'">
                <button @click="completeLesson" class="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-lg transition-all">
                  Mark as Completed
                </button>
              </div>
              <div v-else class="p-4 bg-blue-50 border border-blue-100 rounded-xl text-blue-800 text-sm">
                <p>Complete the task or quiz to finish this lesson.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <AiChat :lessonContext="lesson" />
  </div>
</template>

<style>
.fade-enter-active, .fade-leave-active {
  transition: all 0.4s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin-slow {
  animation: spin-slow 3s linear infinite;
}
</style>