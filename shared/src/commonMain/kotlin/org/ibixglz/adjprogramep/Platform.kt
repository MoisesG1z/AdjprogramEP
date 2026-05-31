package org.ibixglz.adjprogramep

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform