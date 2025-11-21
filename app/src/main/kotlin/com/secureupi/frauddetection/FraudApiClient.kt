package com.secureupi.frauddetection

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class FraudResult(
    val trustScore: Int,
    val action: String,
    val reasons: List<String>,
    val subscores: Map<String, Double>
)

class FraudApiClient(private val baseUrl: String) {

    suspend fun checkFraud(
        payerVpa: String,
        payeeVpa: String,
        amount: Double,
        message: String,
        transactionType: String,
        mobileNumber: String
    ): FraudResult = withContext(Dispatchers.IO) {
        val conn = (URL("$baseUrl/api/v1/score_request").openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("Content-Type", "application/json")
            doOutput = true
            connectTimeout = 6000
            readTimeout = 6000
        }

        val body = JSONObject().apply {
            put("transaction_id", "android_${System.currentTimeMillis()}")
            put("payer_vpa", payerVpa)
            put("payee_vpa", payeeVpa)
            put("mobile_number", mobileNumber)
            put("amount", amount)
            put("message", message)
            put("transaction_type", transactionType)
            put("payee_new", 1)
        }.toString()

        conn.outputStream.use { it.write(body.toByteArray()) }
        val text = conn.inputStream.bufferedReader().readText()
        conn.disconnect()

        val json = JSONObject(text)
        val subs = json.getJSONObject("subscores")
        val reasonsArr = json.getJSONArray("reasons")
        FraudResult(
            trustScore = json.getInt("trust_score"),
            action = json.getString("action"),
            reasons = List(reasonsArr.length()) { reasonsArr.getString(it) },
            subscores = mapOf(
                "phishing" to subs.getDouble("phishing"),
                "quishing" to subs.getDouble("quishing"),
                "collect" to subs.getDouble("collect"),
                "malware" to subs.getDouble("malware")
            )
        )
    }
}
