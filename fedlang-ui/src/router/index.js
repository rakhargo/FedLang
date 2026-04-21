import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/my-projects',
      name: 'my-projects',
      component: () => import('../views/MyProjectsView.vue'),
    },
    {
      path: '/project/:id',
      name: 'project-detail',
      component: () => import('../views/ProjectDetail.vue'),
    },
    {
      path: '/submit/:id',
      name: 'submit-update',
      component: () => import('../views/SubmitUpdate.vue'),
    },
  ],
})

export default router
