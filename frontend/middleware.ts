export { default } from "next-auth/middleware";

export const config = {
    // 보호할 경로 지정 (Matcher)
    // 1. /mypage: 마이페이지 전체
    // 2. /board/write: 글쓰기 페이지
    // 3. /community/write: (혹시 모를) 커뮤니티 글쓰기
    matcher: [
        // "/mypage/:path*", // DISABLED: Allow access without login
        // "/board/write",   // DISABLED: Allow access without login
        // "/community/write",
    ],
};
