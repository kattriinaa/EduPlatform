import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { hideNavbar: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
  },
  {
    path: '/course/:id',
    name: 'CoursePage',
    component: () => import('../views/CoursePage.vue')
  },
  {
    path: '/calendar',
    name: 'CalendarPage',
    component: () => import('../views/CalendarPage.vue')
  },
  {
    path: '/library',
    name: 'Library',
    component: () => import('../views/Library.vue')
  },
  {
    path: '/course/:courseId/lesson/:lessonId',
    name: 'LessonPage',
    component: () => import('../views/LessonPage.vue'),
    props: true
  },
  {
    path: '/instructor/review',
    name: 'InstructorReview',
    component: () => import('../views/InstructorReview.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  { 
    path: '/instructor/create-course',
    name: 'CreateCourse',
    component: () => import('../views/CreateCourse.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: () => import('../views/Assignments.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: routes,
})

export default router
