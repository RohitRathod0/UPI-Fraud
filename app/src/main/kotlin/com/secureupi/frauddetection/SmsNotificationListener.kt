package com.secureupi.frauddetection

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class SmsNotificationListener : NotificationListenerService() {

    companion object {
        private const val TAG = "SecureUPI_Listener"
        private val SMS_PACKAGES = setOf(
            "com.google.android.apps.messaging",
            "com.samsung.android.messaging",
            "com.android.messaging"
        )
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null) return
        if (!SMS_PACKAGES.contains(sbn.packageName)) return

        val extras = sbn.notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE) ?: ""
        val text = extras.getString(Notification.EXTRA_TEXT) ?: ""
        val bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString() ?: text
        val subText = extras.getString(Notification.EXTRA_SUB_TEXT) ?: ""
        val fullMessage = "$title $bigText $subText".trim()

        Log.d(TAG, "From: $title")
        Log.d(TAG, "Msg: $fullMessage")

        if (isPaymentMessage(fullMessage)) {
            CoroutineScope(Dispatchers.IO).launch {
                runCatching {
                    val parsed = MessageParser().parseMessage(fullMessage)
                    val api = FraudApiClient(BuildConfig.API_BASE_URL)
                    val result = api.checkFraud(
                        payerVpa = parsed.payerVpa,
                        payeeVpa = parsed.payeeVpa,
                        amount = parsed.amount,
                        message = fullMessage,
                        transactionType = parsed.transactionType,
                        mobileNumber = parsed.mobileNumber
                    )
                    if (result.action == "WARN" || result.action == "BLOCK" || result.action == "HUMAN_REVIEW") {
                        AlertHelper(this@SmsNotificationListener).showFraudNotification(
                            trustScore = result.trustScore,
                            action = result.action,
                            reasons = result.reasons,
                            originalSender = title.ifBlank { "Unknown" }
                        )
                    }
                }.onFailure { e ->
                    Log.e(TAG, "Fraud analysis failed: ${e.message}")
                }
            }
        }
    }

    private fun isPaymentMessage(message: String): Boolean {
        val kws = listOf(
            "upi","paytm","phonepe","gpay","bhim","₹","rs","amount",
            "paid","received","transaction","payment","collect","qr","scan"
        )
        val m = message.lowercase()
        return kws.any { m.contains(it) }
    }
}
