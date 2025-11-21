package com.secureupi.frauddetection

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.core.app NotificationCompat
import androidx.core.app.NotificationManagerCompat

class AlertHelper(private val context: Context) {

    companion object {
        private const val CHANNEL_ID = "fraud_alerts"
        private const val CHANNEL_NAME = "Fraud Alerts"
        private const val NOTIFICATION_ID = 1001
    }

    init { createChannel() }

    private fun createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            val ch = NotificationChannel(CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_HIGH)
            ch.description = "Alerts for potential payment fraud"
            nm.createNotificationChannel(ch)
        }
    }

    fun showFraudNotification(
        trustScore: Int,
        action: String,
        reasons: List<String>,
        originalSender: String
    ) {
        val (title, color, priority) = when (action) {
            "BLOCK" -> Triple("FRAUD DETECTED - DO NOT PAY!", 0xFFD32F2F.toInt(), NotificationCompat.PRIORITY_MAX)
            "HUMAN_REVIEW" -> Triple("Suspicious Payment Detected", 0xFFF57C00.toInt(), NotificationCompat.PRIORITY_HIGH)
            "WARN" -> Triple("Payment Warning", 0xFFFBC02D.toInt(), NotificationCompat.PRIORITY_HIGH)
            else -> Triple("Payment Verified", 0xFF388E3C.toInt(), NotificationCompat.PRIORITY_DEFAULT)
        }

        val reasonsText = reasons.joinToString("\n• ", prefix = "• ")
        val notif = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText("Trust Score: $trustScore/100 | From: $originalSender")
            .setStyle(NotificationCompat.BigTextStyle()
                .bigText("Trust Score: $trustScore/100\n\nReasons:\n$reasonsText"))
            .setColor(color)
            .setPriority(priority)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(context).notify(NOTIFICATION_ID, notif)
    }
}
