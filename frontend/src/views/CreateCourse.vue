<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Plus, 
  Trash2, 
  Wand2, 
  Save, 
  ChevronLeft, 
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Layout,
  Calendar,
  X
} from 'lucide-vue-next'
import { computed } from 'vue'

const router = useRouter()
const isLoadingAI = ref(false)
const syllabusText = ref('')

const modal = reactive({
  show: false,
  title: '',
  message: '',
  type: 'info', // 'success', 'error', 'info'
  onClose: null
})

const showAlert = (title, message, type = 'info', onClose = null) => {
  modal.title = title
  modal.message = message
  modal.type = type
  modal.show = true
  modal.onClose = onClose
}

const closeModal = () => {
  modal.show = false
  if (modal.onClose) modal.onClose()
}

const storedId = localStorage.getItem('userId');
const storedName = localStorage.getItem('userName');
const isLogged = localStorage.getItem('isLoggedIn');

const teacherId = storedId ? Number(storedId) : null;
const teacherName = storedName || null;

const createEmptyLesson = () => ({
  title: '',
  content: '',
  assignment: '',
  assignmentType: 'text', 
  quizOptions: ['', ''] 
})

const course = ref({
  title: '',
  description: '',
  startDate: '',
  endDate: '', 
  imageUrl: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&h=400&fit=crop',
  modules: [
    {
      title: 'Module 1',
      lessons: [
        { title: '', content: '', assignment: '', assignmentType: 'text', quizOptions: ['', ''] }
      ]
    }
  ]
})

const addLesson = (moduleIndex) => {
  course.value.modules[moduleIndex].lessons.push(createEmptyLesson())
}

const removeLesson = (moduleIndex, lessonIndex) => {
  if (course.value.modules[moduleIndex].lessons.length > 1) {
    course.value.modules[moduleIndex].lessons.splice(lessonIndex, 1)
  }
}

const addModule = () => {
  course.value.modules.push({
    title: `Module ${course.value.modules.length + 1}`,
    lessons: [createEmptyLesson()]
  })
}

const removeModule = (index) => {
  if (course.value.modules.length > 1) {
    course.value.modules.splice(index, 1)
  }
}

const generateWithAI = async () => {
  const today = new Date();
  if (!syllabusText.value) return showAlert('Empty Syllabus', 'Please paste a syllabus first!', 'error');
  
  isLoadingAI.value = true;
  try {
    const response = await fetch('http://127.0.0.1:8000/api/ai/generate-course', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        syllabus: syllabusText.value,
        start_date: course.value.startDate,  
        end_date: course.value.endDate 
       })
    });

    if (response.ok) {
      const aiResult = await response.json();
      console.log("Отримані дані від ШІ:", aiResult);
      
      course.value.title = aiResult.title || '';
      course.value.description = aiResult.description || '';

      if (aiResult.modules && Array.isArray(aiResult.modules)) {
        course.value.modules = aiResult.modules.map((mod, mIdx) => ({
          title: mod.title || `Module ${mIdx + 1}`,
          lessons: (mod.lessons || []).map((l, lIdx) => {
            
            let finalAssignmentText = '';
            if (l.type === 'assignment') {
              finalAssignmentText = l.assignment_instruction || '';
            } else if (l.type === 'quiz') {
              finalAssignmentText = l.quiz?.questions?.[0]?.question || 'Quiz Lesson';
            }

            return {
              id: l.id || Date.now() + Math.random(),
              title: l.title || 'Untitled Lesson',
              content: l.content || '', 
              assignment: finalAssignmentText, 
              assignmentType: l.type || 'text',
              duration: l.duration?.replace(/[^0-9]/g, '') || "20",
              quizOptions: l.quiz?.questions?.[0]?.options || ['', '', '', ''],
              correctAnswer: l.quiz?.questions?.[0]?.correctAnswer || 0,
              scheduled_date: l.scheduled_date || null,
              days_offset: lIdx * 2 
            };
          })
        }));
      }

      showAlert('Success!', 'AI Generation complete! Course structured by modules.', 'success');
    } else {
      showAlert('Server Error', 'Server error during AI generation.', 'error');
    }
  } catch (err) {
    console.error(err);
    showAlert('Connection Error', 'Could not reach the server.', 'error');
  } finally {
    isLoadingAI.value = false;
  }
}

const saveCourse = async () => {
  if (!course.value.title) return showAlert('Missing Title', 'Please enter a course title.', 'error');
  
  try {
    const formattedCourse = {
      id: Math.floor(Math.random() * 1000000),
      teacher_id: teacherId,
      teacher: teacherName, 
      title: course.value.title,
      description: course.value.description,
      rating: 0.0,
      students: 0,
      duration: "Variable",
      image: course.value.imageUrl || "https://via.placeholder.com/400",
      enrolled_students: [],
      modules: course.value.modules.map((mod, mIdx) => ({
        id: mIdx + 1,
        title: mod.title || `Module ${mIdx + 1}`,
        lessons: mod.lessons.map((lesson, lIdx) => {
          const courseStart = course.value.startDate 
            ? new Date(course.value.startDate) 
            : new Date()
          const lessonDate = new Date(courseStart)
          lessonDate.setDate(courseStart.getDate() + (lesson.days_offset || lIdx * 2))
          const lessonData = {
            id: (mIdx * 100) + lIdx,
            title: lesson.title,
            duration: lesson.duration,
            content: lesson.content,
            type: lesson.assignmentType,
            assignment_instruction: lesson.assignmentType === 'assignment' ? lesson.assignment : null,
            videoUrl: lesson.videoUrl || null,
            videoDescription: null,
            quiz: null,
            days_offset: lesson.days_offset || (lIdx * 2),
            scheduled_date: lessonDate.toISOString().split('T')[0],
            is_event: lesson.is_event || false,
            assignmentType: lesson.assignmentType || 'text'
          };

          if (lesson.assignmentType === 'quiz') {
            lessonData.quiz = {
              questions: [
                {
                  question: lesson.title,
                  options: lesson.quizOptions,
                  correctAnswer: lesson.correctAnswer || 0
                }
              ]
            };
          }
          return lessonData;
        })
      }))
    };

    console.log("Sending to server:", formattedCourse);

    const response = await fetch('http://127.0.0.1:8000/api/courses/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formattedCourse)
    });

    if (response.ok) {
      const events = []
      formattedCourse.modules.forEach(mod => {
        mod.lessons.forEach(lesson => {
          if (lesson.scheduled_date) { 
            events.push({
              title: lesson.title,
              course_id: formattedCourse.id,
              course: formattedCourse.title,
              type: 'lecture',
              day: lesson.scheduled_date,
              color: 'bg-blue-100 text-blue-800'
            })
          }
        })
      })

      for (const event of events) {
        await fetch('http://127.0.0.1:8000/api/events/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(event)
        })
      }

      showAlert('Success!', 'Course published!', 'success')
      router.push('/dashboard')
    } else {
      const errorData = await response.json();
      console.error("Validation Error:", errorData);
      showAlert('Error', 'Failed to save. Check fields.', 'error');
    }
  } catch (err) {
    console.error("Save Error:", err);
    showAlert('Error', 'Connection lost.', 'error');
  }
}

const isCourseComplete = computed(() => {
  if (!course.value.title || !course.value.description) return false;
  
  return course.value.modules.every(mod => {
    if (!mod.title) return false;
    return mod.lessons.every(lesson => {
      const hasTitle = !!lesson.title;
      const hasContent = lesson.assignmentType === 'text' ? !!lesson.content : true;
      const hasAssignment = lesson.assignmentType === 'assignment' ? !!lesson.assignment : true;
      return hasTitle && (hasContent || hasAssignment);
    });
  });
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <div class="max-w-5xl mx-auto p-6 flex justify-between items-center">
      <button @click="router.back()" class="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors font-medium">
        <ChevronLeft class="w-5 h-5" /> Back to Dashboard
      </button>
      <button 
        @click="saveCourse" 
        :disabled="!isCourseComplete"
        class="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold transition-all flex items-center gap-2"
        :class="{'opacity-50 grayscale cursor-not-allowed': !isCourseComplete, 'hover:bg-indigo-700 shadow-md': isCourseComplete}"
      >
        <Save class="w-5 h-5" /> 
        {{ isCourseComplete ? 'Publish Course' : 'Fill Required Fields' }}
      </button>
    </div>

    <div class="max-w-5xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-1 space-y-6">
        <div class="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm shadow-purple-100/50">
          <h2 class="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">
            <Wand2 class="w-5 h-5 text-purple-600" /> AI Generator
          </h2>
          <textarea v-model="syllabusText" class="w-full p-4 border border-gray-100 bg-gray-50 rounded-2xl text-sm focus:ring-2 focus:ring-purple-500 outline-none transition-all mb-4" rows="6" placeholder="e.g. 1. Intro to Python. 2. Data Types..."></textarea>
          <button @click="generateWithAI" :disabled="isLoadingAI" class="w-full bg-purple-600 text-white py-3 rounded-xl font-bold hover:bg-purple-700 disabled:opacity-50 transition-all">
            {{ isLoadingAI ? '🌀 Generating...' : 'Generate Draft' }}
          </button>
        </div>

        <div class="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm">
          <h2 class="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2"><ImageIcon class="w-4 h-4" /> Cover URL</h2>
          <input v-model="course.imageUrl" type="text" class="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl text-xs outline-none mb-3">
          <div class="rounded-xl overflow-hidden aspect-video border border-gray-100">
            <img :src="course.imageUrl || 'https://via.placeholder.com/400x225?text=No+Image'" class="w-full h-full object-cover">
          </div>
        </div>
      </div>

      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white p-8 rounded-3xl border border-gray-200 shadow-sm space-y-5">
          <input v-model="course.title" type="text" class="w-full text-2xl font-bold bg-transparent border-b-2 border-gray-100 focus:border-indigo-500 outline-none pb-2" placeholder="Course Title">
          <textarea v-model="course.description" class="w-full p-4 bg-gray-50 rounded-xl border-none text-sm outline-none focus:ring-1 focus:ring-gray-200" rows="3" placeholder="Description"></textarea>

          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100">
              <span class="text-[10px] font-black text-gray-400 uppercase block mb-1">Start Date</span>
              <input v-model="course.startDate" type="date" class="w-full bg-transparent font-bold text-indigo-700 outline-none" lang="en">
            </div>
            <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100">
              <span class="text-[10px] font-black text-gray-400 uppercase block mb-1">End Date</span>
              <input v-model="course.endDate" type="date" class="w-full bg-transparent font-bold text-indigo-700 outline-none" lang="en">
            </div>
          </div>
        </div>

        <div class="space-y-8">
          <div class="flex justify-between items-center px-2">
            <h2 class="text-lg font-bold text-gray-800">Course Syllabus</h2>
            <button @click="addModule" class="text-xs bg-indigo-600 text-white px-4 py-2 rounded-xl font-bold hover:bg-indigo-700 flex items-center gap-2 shadow-sm transition-all">
              <Plus class="w-4 h-4" /> Add Module
            </button>
          </div>

          <div v-for="(module, mIndex) in course.modules" :key="mIndex" class="space-y-4 p-6 bg-gray-100/40 rounded-[2rem] border border-gray-200">
            
            <div class="flex justify-between items-center mb-2 px-2">
              <div class="flex items-center gap-2 flex-1">
                <Layout class="w-4 h-4 text-indigo-500" />
                <input v-model="module.title" class="bg-transparent font-black text-indigo-900 uppercase tracking-widest outline-none border-b border-transparent focus:border-indigo-300 w-full text-sm" placeholder="Module Name">
              </div>
              <button @click="removeModule(mIndex)" class="text-gray-400 hover:text-red-500 transition-colors ml-4">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>

            <div v-for="(lesson, lIndex) in module.lessons" :key="lIndex" class="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm relative group transition-all hover:shadow-md">

              <div class="flex items-center gap-3 mb-6">
                <span class="w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold text-xs">{{ lIndex + 1 }}</span>
                <input v-model="lesson.title" class="text-lg font-bold bg-transparent border-none focus:outline-none w-full" placeholder="Lesson Title">
                <button @click="removeLesson(mIndex, lIndex)" class="absolute top-6 right-6 text-gray-200 hover:text-red-500 transition-colors">
                  <Trash2 class="w-5 h-5" />
                </button>
              </div>

              <div class="grid grid-cols-2 gap-4 mb-4">
                <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100">
                   <span class="text-[10px] font-black text-gray-400 uppercase block mb-1">Duration (min)</span>
                   <input v-model="lesson.duration" type="number" class="w-full bg-transparent font-bold text-indigo-700 outline-none" placeholder="E.g. 20">
                </div>
                <div class="bg-gray-50 p-3 rounded-2xl border border-gray-100">
                   <span class="text-[10px] font-black text-gray-400 uppercase block mb-1">Schedule Date</span>
                   <input v-model="lesson.scheduled_date" type="date" class="w-full bg-transparent font-bold text-indigo-700 outline-none cursor-pointer" lang="en">
                </div>
              </div>

              <div class="mb-4">
                <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2 px-1 tracking-widest">Video Embed URL (YouTube)</label>
                <input 
                  v-model="lesson.videoUrl" 
                  type="text" 
                  class="w-full p-3 bg-gray-50 rounded-xl border border-gray-100 text-xs outline-none focus:ring-2 focus:ring-indigo-500" 
                  placeholder="https://www.youtube.com/embed/..."
                >
              </div>

              <div class="space-y-4">
                <div>
                  <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest block mb-2 px-1">Lesson Material</label>
                  <textarea v-model="lesson.content" rows="4" class="w-full p-4 bg-gray-50 rounded-2xl border-none text-sm outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Lesson details..."></textarea>
                </div>

                <div class="p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100">
                  <div class="flex justify-between items-center mb-3">
                    <label class="text-[10px] font-black text-indigo-500 uppercase tracking-widest px-1">Assignment Type</label>
                    <select v-model="lesson.assignmentType" class="text-[10px] font-bold border-none bg-white rounded-lg px-2 py-1 shadow-sm outline-none text-indigo-600 uppercase">
                      <option value="text">Written</option>
                      <option value="code">Code</option>
                      <option value="quiz">Quiz</option>
                    </select>
                  </div>

                  <div v-if="lesson.assignmentType !== 'quiz'">
                    <textarea v-model="lesson.assignment" class="w-full p-3 bg-white rounded-xl border-none focus:ring-2 focus:ring-indigo-500 outline-none text-sm" :placeholder="lesson.assignmentType === 'code' ? 'Describe the coding challenge...' : 'Assignment instruction...'" rows="2"></textarea>
                  </div>
                  <div v-else class="space-y-2">
                    <input v-model="lesson.assignment" class="w-full p-3 bg-white rounded-xl border-none text-sm outline-none" placeholder="Quiz Question">
                    <div class="grid grid-cols-2 gap-2 mt-2">
                      <input v-for="(opt, oIdx) in 2" :key="oIdx" v-model="lesson.quizOptions[oIdx]" class="p-2 bg-white rounded-lg text-xs border border-indigo-50 outline-none focus:ring-1 focus:ring-indigo-500" :placeholder="'Option ' + (oIdx === 0 ? 'A' : 'B')">
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <button @click="addLesson(mIndex)" class="w-full py-3 border-2 border-dashed border-indigo-200 rounded-2xl text-indigo-500 font-bold text-xs hover:bg-indigo-50 transition-all flex justify-center items-center gap-2">
                <Plus class="w-4 h-4" /> Add Lesson to {{ module.title || 'Module' }}
              </button>
          </div>
        </div>
      </div>

      <Transition name="fade">
        <div v-if="modal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div class="bg-white rounded-3xl max-w-sm w-full p-6 shadow-2xl">
            <div class="flex flex-col items-center text-center">
              <div :class="['p-3 rounded-full mb-4', modal.type === 'success' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600']">
                <CheckCircle2 v-if="modal.type === 'success'" class="w-8 h-8" />
                <AlertCircle v-else class="w-8 h-8" />
              </div>
              <h3 class="text-xl font-bold text-gray-900 mb-2">{{ modal.title }}</h3>
              <p class="text-gray-500 text-sm mb-6">{{ modal.message }}</p>
              <button @click="closeModal" class="w-full py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-gray-800 transition-colors">Got it</button>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.v-enter-active, .v-leave-active {
  transition: opacity 0.3s ease;
}
.v-enter-from, .v-leave-to {
  opacity: 0;
}
</style>