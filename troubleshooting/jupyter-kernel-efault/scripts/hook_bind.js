const bind = Module.getExportByName('ws2_32.dll', 'bind');

Interceptor.attach(bind, {
  onEnter: function (args) {
    this.sockaddr = args[1];
    this.family = this.sockaddr.readU16();
    this.port = this.sockaddr.add(2).readU16(); // big-endian
  },
  onLeave: function (retval) {
    const ret = retval.toInt32();
    if (ret !== 0) {
      // WSAGetLastError는 별도 export라 여기선 생략, ret != 0이면 일단 로그
      console.log(`[FAIL] bind() ret=${ret}, family=${this.family}, port=${this.port}`);
      console.log(Thread.backtrace(this.context, Backtracer.ACCURATE)
        .map(DebugSymbol.fromAddress).join('\n'));
    }
  }
});