<template>
  <div class="flex justify-between gap-3 border-t px-4 py-2.5 sm:px-10">
    <div class="flex gap-1.5">
      <Button
        ref="sendEmailRef"
        variant="ghost"
        :class="[
          showEmailBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        :label="__('Reply')"
        :iconLeft="Email2Icon"
        @click="toggleEmailBox()"
      />
      <Button
        variant="ghost"
        :label="__('Comment')"
        :class="[
          showCommentBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
        ]"
        :iconLeft="CommentIcon"
        @click="toggleCommentBox()"
      />
    </div>
  </div>
  <div
    v-show="showEmailBox"
    @keydown.ctrl.enter.capture.stop="submitEmail"
    @keydown.meta.enter.capture.stop="submitEmail"
  >
    <EmailEditor
      ref="newEmailEditor"
      v-model:content="newEmail"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitEmail,
        disabled: emailEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showEmailBox = false
          newEmailEditor.subject = subject
          newEmailEditor.toEmails = doc.email ? [doc.email] : []
          newEmailEditor.ccEmails = []
          newEmailEditor.bccEmails = []
          newEmailEditor.cc = false
          newEmailEditor.bcc = false
          newEmail = ''
        },
      }"
      :editable="showEmailBox"
      v-model="doc"
      v-model:attachments="attachments"
      :doctype="doctype"
      :subject="subject"
      :placeholder="
        __('Hi John, \n\nCan you please provide more details on this...')
      "
    />
  </div>
  <div v-show="showCommentBox">
    <CommentBox
      ref="newCommentEditor"
      v-model:content="newComment"
      :submitButtonProps="{
        variant: 'solid',
        onClick: submitComment,
        disabled: commentEmpty,
      }"
      :discardButtonProps="{
        onClick: () => {
          showCommentBox = false
          newComment = ''
        },
      }"
      :editable="showCommentBox"
      v-model="doc"
      v-model:attachments="attachments"
      :doctype="doctype"
      :placeholder="__('@John, can you please check this?')"
    />
  </div>
</template>

<script setup>
import EmailEditor from '@/components/EmailEditor.vue'
import CommentBox from '@/components/CommentBox.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import { capture } from '@/telemetry'
import { usersStore } from '@/stores/users'
import { useStorage } from '@vueuse/core'
import { call, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const doc = defineModel()
const reload = defineModel('reload')

const emit = defineEmits(['scroll'])

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const showEmailBox = ref(false)
const showCommentBox = ref(false)
const newEmail = useStorage('emailBoxContent', '')
const newComment = useStorage('commentBoxContent', '')
const newEmailEditor = ref(null)
const newCommentEditor = ref(null)
const sendEmailRef = ref(null)
const attachments = ref([])
const subject = ref('')

const signature = createResource({
  url: 'crm.api.get_user_signature',
  cache: 'user-email-signature',
  auto: true,
})

// Make hrefs absolute/safe
function normalizeHref(href) {
  if (!href) return ''
  const s = href.trim()
  if (/^(javascript|vbscript):/i.test(s)) return ''
  if (/^data:(?!image\/)/i.test(s)) return ''
  if (/^(https?:|ftp:|mailto:|tel:|cid:)/i.test(s)) return s
  if (s.startsWith('//')) return `https:${s}`
  if (s.startsWith('/')) {
    try { return new URL(s, window.location.origin).href } catch { return s }
  }
  if (s.startsWith('#')) return s
  return `https://${s.replace(/^https?:\/\//i, '')}`
}

function setSignature(editor) {
  if (!signature.data) return

  // Avoid duplicates: only insert when empty
  let emailContent = editor.getHTML() || ''
  emailContent = emailContent.startsWith('<p></p>') ? emailContent.slice(7) : emailContent
  const isEmpty = !emailContent || emailContent === '<p></p>'
  if (!isEmpty) {
    editor.commands.focus('start')
    return
  }

  let raw = String(signature.data).replace(/\n/g, '<br>')
  try {
    const parser = new DOMParser()
    const parsed = parser.parseFromString(raw, 'text/html')
    const ql = parsed.querySelector('.ql-editor')
    const container = document.createElement('div')
    container.innerHTML = ql ? ql.innerHTML : parsed.body.innerHTML

    // Unwrap invalid p>div nesting
    container.innerHTML = container.innerHTML.replace(
      /<p[^>]*>\s*<div[^>]*>([\s\S]*?)<\/div>\s*<\/p>/gi,
      '$1'
    )

    // Absolutize img src and collect attrs for fallback
    const imgNodes = []
    container.querySelectorAll('img').forEach((img) => {
      const src = img.getAttribute('src') || ''
      const isAbs = /^(?:[a-z]+:)?\/\//i.test(src) || src.startsWith('data:') || src.startsWith('cid:')
      const absolute = isAbs ? src : new URL(src, window.location.origin).href
      if (absolute !== src) img.setAttribute('src', absolute)
      imgNodes.push({
        src: absolute,
        alt: img.getAttribute('alt') || null,
        title: img.getAttribute('title') || null,
        width: img.getAttribute('width') || null,
        height: img.getAttribute('height') || null,
        style: img.getAttribute('style') || null,
        class: img.getAttribute('class') || null,
      })
    })

    // Normalize all links
    container.querySelectorAll('a').forEach((a) => {
      const href = a.getAttribute('href') || ''
      const normalized = normalizeHref(href)
      if (normalized) a.setAttribute('href', normalized)
      a.setAttribute('target', '_blank')
      const rel = new Set((a.getAttribute('rel') || '').split(/\s+/).filter(Boolean))
      rel.add('noopener'); rel.add('noreferrer')
      a.setAttribute('rel', Array.from(rel).join(' '))
    })

    // Normalize empty lines to <p></p> to avoid double breaks
    let cleaned = container.innerHTML.replace(/<p>\s*<br\s*\/?>\s*<\/p>/gi, '<p></p>')

    // Exactly two blank lines before signature
    const twoBlank = '<p></p><p></p>'
    const wrappedSignature = `<div class="signature" data-signature="true">${cleaned}</div>`

    editor.commands.setContent(`${twoBlank}${wrappedSignature}`)

    // Fallback: if editor dropped <img>, re-insert as nodes (preserves size attrs)
    const hasImg = /<img\b/i.test(editor.getHTML())
    if (!hasImg && imgNodes.length) {
      imgNodes.forEach(({ src, alt, width, height, style, class: klass }) => {
        const attrs = { src }
        if (alt) attrs.alt = alt
        if (width) attrs.width = width
        if (height) attrs.height = height
        if (style) attrs.style = style
        if (klass) attrs.class = klass
        editor.commands.insertContent({ type: 'image', attrs })
      })
    }
  } catch {
    const twoBlank = '<p></p><p></p>'
    editor.commands.setContent(`${twoBlank}<div class="signature" data-signature="true">${raw}</div>`)
  }

  editor.commands.focus('start')
}

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      let editor = newEmailEditor.value.editor
      editor.commands.focus()
      setSignature(editor)
    }
  },
)

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      newCommentEditor.value.editor.commands.focus()
    }
  },
)

const commentEmpty = computed(() => {
  return !newComment.value || newComment.value === '<p></p>'
})

const emailEmpty = computed(() => {
  return (
    !newEmail.value ||
    newEmail.value === '<p></p>' ||
    !newEmailEditor.value?.toEmails?.length
  )
})

async function sendMail() {
  let recipients = newEmailEditor.value.toEmails
  let subject = newEmailEditor.value.subject
  let cc = newEmailEditor.value.ccEmails || []
  let bcc = newEmailEditor.value.bccEmails || []

  if (attachments.value.length) {
    capture('email_attachments_added')
  }
  await call('frappe.core.doctype.communication.email.make', {
    recipients: recipients.join(', '),
    attachments: attachments.value.map((x) => x.name),
    cc: cc.join(', '),
    bcc: bcc.join(', '),
    subject: subject,
    content: newEmail.value,
    doctype: props.doctype,
    name: doc.value.name,
    send_email: 1,
    sender: getUser().email,
    sender_full_name: getUser()?.full_name || undefined,
  })
}

async function sendComment() {
  let comment = await call('frappe.desk.form.utils.add_comment', {
    reference_doctype: props.doctype,
    reference_name: doc.value.name,
    content: newComment.value,
    comment_email: getUser().email,
    comment_by: getUser()?.full_name || undefined,
  })
  if (comment && attachments.value.length) {
    capture('comment_attachments_added')
    await call('crm.api.comment.add_attachments', {
      name: comment.name,
      attachments: attachments.value.map((x) => x.name),
    })
  }
}

async function submitEmail() {
  if (emailEmpty.value) return
  showEmailBox.value = false
  await sendMail()
  newEmail.value = ''
  reload.value = true
  emit('scroll')
  capture('email_sent', { doctype: props.doctype })
  updateOnboardingStep('send_first_email')
}

async function submitComment() {
  if (commentEmpty.value) return
  showCommentBox.value = false
  await sendComment()
  newComment.value = ''
  reload.value = true
  emit('scroll')
  capture('comment_sent', { doctype: props.doctype })
  updateOnboardingStep('add_first_comment')
}

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false
  }
  showEmailBox.value = !showEmailBox.value
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false
  }
  showCommentBox.value = !showCommentBox.value
}

defineExpose({
  show: showEmailBox,
  showComment: showCommentBox,
  editor: newEmailEditor,
})
</script>

<style>
/* Remove extra margins added by the image node-view in the editor */
.tiptap .signature .not-prose.my-6 {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

.tiptap .signature [data-node-view-wrapper] {
  margin: 0 !important;
}

/* Keep image width from the signature and don't constrain it */
.tiptap .signature img {
  max-width: none;
  height: auto;
}
</style>
