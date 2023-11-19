export class TimeSpan {
    constructor(milliseconds: number = 0) {
        this._ms = milliseconds;
        this.check();
    }

    private check() {
        if (this._ms < 0) {
            this._ms = 0;
        }
    }

    public static add(...ts: TimeSpan[]) {
        let total = 0;
        for (let t of ts) {
            total += t._ms;
        }
        return new TimeSpan(total);
    }

    public add(...ts: TimeSpan[]) {
        let total = 0;
        for (let t of ts) {
            total += t._ms;
        }
        this._ms += total;
        this.check();
        return this;
    }

    public sub(...ts: TimeSpan[]) {
        let total = 0;
        for (let t of ts) {
            total += t._ms;
        }
        this._ms -= total;
        this.check();
        return this;
    }

    public static sub(a: TimeSpan, b: TimeSpan) {
        return new TimeSpan(a.milliseconds - b.milliseconds);
    }

    // b must be later in time than a, otherwise the TimeSpan will be zero
    public static fromDateDiff(a: Date, b: Date) {
        return new TimeSpan(b.getTime() - a.getTime());
    }

    public static fromMilliseconds(milliseconds: number) {
        return new TimeSpan(milliseconds);
    }

    public static fromSeconds(seconds: number) {
        return new TimeSpan(seconds * 1000);
    }

    public static fromMinutes(minutes: number) {
        return new TimeSpan(minutes * 60 * 1000);
    }

    public static fromHours(hours: number) {
        return new TimeSpan(hours * 60 * 60 * 1000);
    }

    public static fromDays(days: number) {
        return new TimeSpan(days * 24 * 60 * 60 * 1000);
    }

    public get milliseconds(): number {
        return this._ms;
    }

    public get seconds(): number {
        return this._ms / 1000;
    }

    public get minutes(): number {
        return this._ms / (1000 * 60);
    }

    public get hours(): number {
        return this._ms / (1000 * 60 * 60);
    }

    public get days(): number {
        return this._ms / (1000 * 60 * 60 * 24);
    }

    private _ms: number;
}
