import { defineStore } from 'pinia'
import { ref } from 'vue'
import { get, post, patch, put, del } from '@/composables/api'

export interface OrderItem {
  id: number
  product_id: number
  quantity: number
  unit_price: number
  is_free: boolean
  product_name?: string
}

export interface Order {
  id: number
  customer_name: string
  customer_phone?: string
  address_street?: string
  address_neighborhood?: string
  address_city?: string
  notes?: string
  payment_status: string
  status: string
  created_by: number
  created_at: string
  delivered_at?: string
  items: OrderItem[]
}

export const useOrderStore = defineStore('orders', () => {
  const orders = ref<Order[]>([])

  async function fetchOrders(params?: { status?: string; payment_status?: string }) {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.payment_status) q.set('payment_status', params.payment_status)
    orders.value = await get<Order[]>(`/orders/?${q}`)
  }

  async function createOrder(data: {
    customer_name: string
    customer_phone?: string
    address_street?: string
    address_neighborhood?: string
    address_city?: string
    notes?: string
    payment_status: string
    items: { product_id: number; quantity: number }[]
  }) {
    return post<Order>('/orders/', data)
  }

  async function updatePayment(orderId: number, payment_status: string) {
    await post<Order>('/payment/', { order_id: orderId, payment_status })
    await fetchOrders()
  }

  async function deliverOrder(orderId: number) {
    await post<Order>('/deliver/', { order_id: orderId })
    await fetchOrders()
  }

  async function reversePayment(orderId: number) {
    await del(`/payment/${orderId}`)
    await fetchOrders()
  }

  async function reverseDelivery(orderId: number) {
    await del(`/deliver/${orderId}`)
    await fetchOrders()
  }

  async function updateOrder(
    orderId: number,
    data: { notes?: string; items: { product_id: number; quantity: number }[] }
  ) {
    await post<Order>('/orders/update', { order_id: orderId, ...data })
    await fetchOrders()
  }

  async function deleteOrder(orderId: number) {
    await del(`/orders/${orderId}`)
    await fetchOrders()
  }

  return { orders, fetchOrders, createOrder, updatePayment, deliverOrder, reversePayment, reverseDelivery, updateOrder, deleteOrder }
})
