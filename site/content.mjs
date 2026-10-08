export const release =
  "https://github.com/shanezchang/sideword/releases/tag/v0.4.0-beta.1";
export const repo = "https://github.com/shanezchang/sideword";
export const command =
  "curl --proto '=https' --tlsv1.2 -fsSL https://github.com/shanezchang/sideword/releases/download/v0.4.0-beta.1/install.sh | /bin/bash";
export const words = [
  {
    name: "adapt",
    ipa: "əˈdæpt",
    meaning: "v. 适应变化；作出调整",
    example: "It can take time to adapt to life in a new country.",
    translation: "适应一个新国家的生活可能需要时间。",
  },
  {
    name: "maintain",
    ipa: "meɪnˈteɪn",
    meaning: "v. 使某种状态持续；维护",
    example: "It is important to maintain a balance between work and rest.",
    translation: "保持工作与休息之间的平衡很重要。",
  },
  {
    name: "environment",
    ipa: "ɪnˈvaɪrənmənt",
    meaning: "n. 环境；周围的条件",
    example: "A quiet environment can help people concentrate.",
    translation: "安静的环境可以帮助人们集中注意力。",
  },
];
export const locales = {
  en: {
    lang: "en",
    path: "/",
    title: "Sideword — Learn English in your terminal",
    description:
      "A free, open-source terminal vocabulary app with Chinese meanings, IPA, Mac pronunciation and spaced review. Download Sideword for Apple Silicon or install from source.",
    skip: "Skip to content",
    nav: ["How it works", "Install", "GitHub"],
    switch: "中文",
    switchPath: "/zh/",
    intro: "English, a little closer.",
    hero: "A few words.\nRight in your terminal.",
    lead: "Meet a word, hear it, understand it. Come back when it’s time to remember. A small learning habit, alongside the work you already do.",
    cta: "Get Sideword for Mac",
    source: "Explore the source",
    availability: "Free & open source. No account needed.",
    demo: "Try the learning loop",
    demoNote: "Interactive web demo · nothing is saved",
    select: "Choose a word",
    remember: "Remembered",
    reset: "Start again",
    remembered: "Set aside for review tomorrow.",
    empty: "A little learned. A little later.",
    emptyText: "These words leave your daily list, not your memory schedule.",
    left: "words to explore",
    loopTitle: "Remembering isn’t\na one-time thing.",
    loopLead:
      "Start with understanding, not a spelling test. Sideword keeps the next small step ready for you.",
    steps: [
      [
        "Read with context",
        "The word, its pronunciation, Chinese meaning and bilingual example, together.",
      ],
      [
        "Listen, then decide",
        "British pronunciation by default on Mac. Mark what you know; keep exploring what you don’t.",
      ],
      [
        "Return at the right time",
        "Remembered words leave the daily queue and reappear for scheduled review. Forget one? It returns sooner.",
      ],
    ],
    timeline: ["Learn", "1 day", "3 days", "7 days", "Keep reviewing"],
    timelineNote:
      "Example intervals after successful reviews. A simple schedule, not a promise of perfect memory.",
    details: [
      [
        "Your pace",
        "Five words per page by default. Set any positive number, even ten.",
      ],
      [
        "Your place",
        "Random learning order, preferences and progress survive the next restart.",
      ],
      [
        "Your machine",
        "Study offline. Books, audio cache and learning records stay local.",
      ],
    ],
    installTitle: "One command.\nThen, a few words.",
    installLead:
      "Apple Silicon (M1 or newer), macOS 14+. Python and dependencies are included.",
    copy: "Copy command",
    copied: "Copied",
    copyFailed: "Copy unavailable. Select and copy the command below.",
    start: "Open a new terminal and type",
    startNow: "Or start immediately with",
    download: "Download the ZIP instead",
    downloadNote:
      "Unzip, then double-click Install.command. No administrator password required.",
    preview: "An honest preview",
    previewText:
      "The Mac download is not yet Apple-notarized. macOS may ask you to explicitly approve it. Never disable system security. The public edition includes 30 original sample words, not a complete IELTS word book.",
    installGuide: "Installation & security guide",
    other: "Linux, Intel Mac, or prefer source?",
    otherText:
      "Use the Python/uv installation in the README. Linux supports learning; pronunciation currently requires macOS. No native Windows release yet.",
    faqTitle: "A few useful answers.",
    faqs: [
      [
        "Is Sideword free?",
        "Yes. The application and its original sample content are open source under MIT. There is no subscription or account.",
      ],
      [
        "Can I add a complete IELTS word book?",
        "You can import compatible JSON word books you are entitled to use. The public download only includes 30 original samples; third-party textbook vocabulary is not redistributed with it.",
      ],
      [
        "Will an update erase my progress?",
        "The installer keeps the application separate from your SQLite learning records and custom books. Updating the application does not replace your data.",
      ],
      [
        "Is the app available in English?",
        "This website is bilingual. The terminal interface currently uses Chinese, designed for Chinese-speaking learners of English.",
      ],
      [
        "Does the website record my learning?",
        "No. The demonstration runs only in this page and resets on reload. There are no website accounts, analytics scripts or learning-data uploads. Hosting providers may retain standard access logs.",
      ],
    ],
    footer: "Made by Shane Chang. Built for the small gaps in a day.",
    guide: "User guide",
    issues: "Feedback",
    privacy: "No account. No learning-data upload.",
    theme: "Change color theme",
  },
  zh: {
    lang: "zh-CN",
    path: "/zh/",
    title: "Sideword — 在终端里学英语的开源单词工具",
    description:
      "Sideword 是免费的开源终端英语学习工具。单词、音标、中文释义、双语例句、Mac 英音发音与间隔复习，一条命令安装，学习记录只留在本地。",
    skip: "跳到正文",
    nav: ["怎么学", "安装", "GitHub"],
    switch: "English",
    switchPath: "/",
    intro: "让英语，离你近一点。",
    hero: "学几个单词，\n就在终端里。",
    lead: "认识一个词，听清它，理解它。到时间，再回来复习。在熟悉的工作环境里，留一点空间给英语。",
    cta: "安装 Mac 版",
    source: "看看源代码",
    availability: "免费、开源，不需要注册。",
    demo: "先试着学一个词",
    demoNote: "网页交互演示 · 不保存学习记录",
    select: "选择单词",
    remember: "记住了",
    reset: "再试一次",
    remembered: "已移出日常列表，明天回来复习。",
    empty: "学会一点，明天再见。",
    emptyText: "记住的词暂时退场，但不会离开复习计划。",
    left: "个词待认识",
    loopTitle: "记住了，\n也值得再见一面。",
    loopLead:
      "先理解，不急着默写。Sideword 帮你把学习拆成随时可以开始的一小步。",
    steps: [
      [
        "先认识",
        "单词、音标、中文释义和双语例句放在一起，先弄懂这个词怎么用。",
      ],
      [
        "听一听，再判断",
        "Mac 默认英音发音。认识了就标记，不熟悉就再看一会儿。",
      ],
      [
        "到时间，再复习",
        "记住的词从日常列表退场，到期再出现。忘记了，就早点回来。",
      ],
    ],
    timeline: ["初次学习", "1 天后", "3 天后", "7 天后", "继续复习"],
    timelineNote:
      "示意：成功复习后的部分间隔。采用简单排程，不承诺神奇的记忆效果。",
    details: [
      ["节奏由你定", "默认一页五词，也可以改成十词，或任何正整数。"],
      ["下次接着来", "随机顺序、阅读位置和偏好都会保留，不用重新开始。"],
      ["只在你本地", "学习无需联网，词库、音频缓存和进度留在自己的电脑。"],
    ],
    installTitle: "一条命令，\n开始学几个词。",
    installLead:
      "适用于 Apple Silicon（M1 及更新芯片），macOS 14+。无需安装 Python 或其他开发环境。",
    copy: "复制命令",
    copied: "已复制",
    copyFailed: "无法自动复制，请选中下方命令手动复制。",
    start: "新开终端，输入",
    startNow: "当前终端也可以直接运行",
    download: "也可以下载 ZIP 安装包",
    downloadNote: "解压后双击 Install.command。安装不需要管理员密码。",
    preview: "先说明白，再开始",
    previewText:
      "Mac 安装包目前是未获 Apple 公证的预览版，系统可能要求单独批准打开。不要关闭系统安全保护。公开版附 30 词原创示例，并非完整的雅思词书。",
    installGuide: "安装与安全提示",
    other: "Linux、Intel Mac，或喜欢从源码安装？",
    otherText:
      "可以使用 README 中的 Python/uv 安装方式。Linux 支持学习，发音目前仅限 macOS；暂不提供 Windows 原生版本。",
    faqTitle: "你可能还想知道。",
    faqs: [
      [
        "真的免费吗？",
        "是的。程序和原创示例内容使用 MIT 开源许可证，没有订阅，也不需要账号。",
      ],
      [
        "可以放进完整的雅思词库吗？",
        "可以导入你有权使用、格式兼容的 JSON 词库。公开安装包只包含 30 词原创示例，不随包分发未经授权的第三方教材词汇。",
      ],
      [
        "升级会丢学习记录吗？",
        "安装器把程序与本地 SQLite 学习记录、自定义词库分开存放。更新程序不会覆盖你的学习数据。",
      ],
      [
        "软件也是中英双语界面吗？",
        "官网支持中文和英文。终端软件目前是中文界面，面向学习英语的中文用户。",
      ],
      [
        "官网会保存我的学习数据吗？",
        "不会。网页演示只在当前页面运行，刷新即重置。官网没有账号、统计脚本，也不上传学习记录；托管服务商可能保留常规访问日志。",
      ],
    ],
    footer: "Shane Chang 制作。给日常的间隙，留几个单词。",
    guide: "使用指南",
    issues: "反馈建议",
    privacy: "不需要账号，不上传学习记录。",
    theme: "切换明暗主题",
  },
};
