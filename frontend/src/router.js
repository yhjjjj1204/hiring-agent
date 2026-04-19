import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('./App.vue'),
  },
  {
    path: '/jobs',
    name: 'JobList',
    component: () => import('./App.vue'),
  },
  {
    path: '/jobs/:job_id',
    name: 'JobDetail',
    component: () => import('./App.vue'),
  },
  {
    path: '/jobs/:job_id/candidates/:candidate_id',
    name: 'CandidateDetail',
    component: () => import('./App.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('./components/NotFound.vue'),
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
