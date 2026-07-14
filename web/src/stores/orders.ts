import { defineStore } from 'pinia'
import { ref } from 'vue'

const API = '/api'

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

  const token = () => localStorage.getItem('token') || ''

  async function fetchOrders(params?: { status?: string; payment_status?: string }) {
    const q = new URLSearchParams()
    if (params?.status) q.set('status', params.status)
    if (params?.payment_status) q.set('payment_status', params.payment_status)
    const res = await fetch(`${API}/orders/?${q}`, {
      headers: { Authorization: `Bearer ${token()}` },
    })
    if (res.ok) orders.value = await res.json()
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
    const res = await fetch(`${API}/orders/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token()}`,
      },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to create order')
    return res.json()
  }

  async function updatePayment(orderId: number, payment_status: string) {
    const res = await fetch(`${API}/orders/${orderId}/payment`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token()}`,
      },
      body: JSON.stringify({ payment_status }),
    })
    if (res.ok) await fetchOrders()
  }

  async function deliverOrder(orderId: number) {
    const res = await fetch(`${API}/orders/${orderId}/deliver`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    if (res.ok) await fetchOrders()
  }

  async function reversePayment(orderId: number) {
    await fetch(`${API}/orders/${orderId}/reverse-payment`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    await fetchOrders()
  }

  async function reverseDelivery(orderId: number) {
    await fetch(`${API}/orders/${orderId}/reverse-delivery`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token()}` },
    })
    await fetchOrders()
  }

  async function updateOrder(
    orderId: number,
    data: { notes?: string; items: { product_id: number; quantity: number }[] }
  ) {
    const res = await fetch(`${API}/orders/${orderId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
      body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error('Failed to update order')
    await fetchOrders()
  }

  async function deleteOrder(orderId: number) {
    const res = await fetch(`${API}/orders/${orderId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token()}` },
    })
    if (!res.ok) throw new Error('Failed to delete order')
    await fetchOrders()
  }

  return { orders, fetchOrders, createOrder, updatePayment, deliverOrder, reversePayment, reverseDelivery, updateOrder, deleteOrder }
})
