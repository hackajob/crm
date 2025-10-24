import { formatDate, timeAgo } from '@/utils'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { getMeta } from '@/stores/meta'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Communication')

export function getSmsLogDetail(row, log, columns = []) {
  if (row === 'sender') {
    return resolveParty('sender', log)
  } else if (row === 'receiver') {
    return resolveParty('receiver', log)
  } else if (row === 'sent_or_received') {
    return {
      label: log.sent_or_received,
      icon: log.sent_or_received === 'Sent' ? 'send' : 'inbox',
    }
  } else if (['modified', 'creation', 'communication_date'].includes(row)) {
    const key = row
    return {
      label: formatDate(log[key] || log.creation),
      timeAgo: __(timeAgo(log[key] || log.creation)),
    }
  }

  let fieldType = columns?.find((col) => (col.key || col.value) == row)?.type

  if (fieldType && ['Date', 'Datetime'].includes(fieldType)) {
    return formatDate(log[row], '', true, fieldType == 'Datetime')
  }

  if (fieldType && fieldType == 'Currency') {
    return getFormattedCurrency(row, log)
  }

  if (fieldType && fieldType == 'Float') {
    return getFormattedFloat(row, log)
  }

  if (fieldType && fieldType == 'Percent') {
    return getFormattedPercent(row, log)
  }

  return log[row]
}

// Caches agent numbers to avoid repeated calls
const _agentNumberCache = {}

async function getAgentNumberForUser(user) {
  if (!user) return ''
  if (_agentNumberCache[user] !== undefined) return _agentNumberCache[user]
  try {
    const res = await call('crm.api.sms.get_agent_numbers', { users: [user] })
    _agentNumberCache[user] = res?.[user] || ''
  } catch (e) {
    _agentNumberCache[user] = ''
  }
  return _agentNumberCache[user]
}

function isSystemUserLike(value) {
  return !!value && (value.includes('@') || value === 'Administrator')
}

function nameFromLeadContext(log) {
  if (log.reference_doctype === 'CRM Lead' && log.reference_name) {
    return {
      label: log.reference_name,
      image: null,
    }
  }
  return null
}

function resolveUserDisplay(userIdOrEmail) {
  const { getUser } = usersStore()
  const u = getUser(userIdOrEmail)
  return {
    label: u?.full_name || userIdOrEmail || __('Unknown'),
    image: u?.user_image || null,
  }
}

function resolveParty(which, log) {
  const dir = log.sent_or_received
  const isSent = dir === 'Sent'
  const isReceived = dir === 'Received'

  if (which === 'sender') {
    if (isSent) {
      return resolveUserDisplay(log.sender)
    } else if (isReceived) {
      const fromLead = nameFromLeadContext(log)
      return fromLead || { label: log.phone_no || __('Unknown'), image: null }
    }
  } else if (which === 'receiver') {
    if (isSent) {
      const toLead = nameFromLeadContext(log)
      return toLead || { label: log.recipients || __('Unknown'), image: null }
    } else if (isReceived) {
      return { label: __('Unknown'), image: null }
    }
  }
  return { label: __('Unknown'), image: null }
}

export async function getFromColumnValue(log) {
  if (log.sent_or_received === 'Sent') {
    if (isSystemUserLike(log.sender)) {
      return (await getAgentNumberForUser(log.sender)) || log.phone_no || ''
    }
    return log.phone_no || ''
  }
  return log.phone_no || ''
}
