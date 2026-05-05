import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
// import CreateProjectView from '../views/CreateProjectView.vue'

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
    {
      path: '/create',
      name: 'create-project',
      // component: CreateProjectView,
      component: () => import('../views/CreateProjectView.vue'),
    }
  ],
})

export default router
