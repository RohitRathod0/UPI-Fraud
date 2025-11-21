package com.secureupi.frauddetection

data class ParsedMessage(
    val payerVpa: String = "",
    val payeeVpa: String = "",
    val amount: Double = 0.0,
    val transactionType: String = "pay",
    val mobileNumber: String = ""
)

class MessageParser {

    private val upiRegex = """[\w.-]+@[\w]+""".toRegex()
    private val amountRegex = """(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.\d{1,2})?)""".toRegex(RegexOption.IGNORE_CASE)
    private val mobileRegex = """(?<!\d)([6-9]\d{9})(?!\d)""".toRegex()

    fun parseMessage(message: String): ParsedMessage {
        val upis = upiRegex.findAll(message).map { it.value }.toList()
        val payeeVpa = upis.firstOrNull().orEmpty()
        val payerVpa = upis.getOrNull(1).orEmpty()

        val amount = amountRegex.find(message)?.groupValues?.get(1)
            ?.replace(",", "")?.toDoubleOrNull() ?: 0.0

        val mobile = mobileRegex.find(message)?.value.orEmpty()

        val txnType = when {
            message.contains("collect", true) -> "collect"
            message.contains("qr", true) || message.contains("scan", true) -> "qr_pay"
            else -> "pay"
        }

        return ParsedMessage(
            payerVpa = payerVpa,
            payeeVpa = payeeVpa,
            amount = amount,
            transactionType = txnType,
            mobileNumber = mobile
        )
    }
}
