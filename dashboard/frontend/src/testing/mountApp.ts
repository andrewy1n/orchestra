import { type Component, flushSync, mount, unmount } from "svelte";
import { vi } from "vitest";

export interface MountedApp {
	instance: ReturnType<typeof mount>;
	unmount: () => void;
}

export interface MountOptions {
	target?: HTMLElement;
	props?: Record<string, unknown>;
}

function describeProblem(value: unknown): string {
	return value instanceof Error ? value.message : String(value);
}

async function settle(): Promise<void> {
	for (let pass = 0; pass < 2; pass += 1) {
		if (vi.isFakeTimers()) {
			await vi.advanceTimersByTimeAsync(0);
		} else {
			await new Promise<void>((resolve) => setTimeout(resolve, 0));
		}
		flushSync();
	}
}

export async function mountApp(
	component: Component<never> | Component<Record<string, never>>,
	options: MountOptions = {},
): Promise<MountedApp> {
	const problems: string[] = [];
	const originalConsoleError = console.error;

	const onError = (event: ErrorEvent) => {
		problems.push(
			`error event: ${describeProblem(event.error ?? event.message)}`,
		);
		event.preventDefault();
	};
	const onRejection = (event: Event) => {
		const reason = (event as Event & { reason?: unknown }).reason;
		problems.push(`unhandled rejection: ${describeProblem(reason)}`);
		event.preventDefault();
	};
	const onProcessRejection = (reason: unknown) => {
		problems.push(`unhandled rejection: ${describeProblem(reason)}`);
	};

	console.error = (...args: unknown[]) => {
		problems.push(`console.error: ${args.map(describeProblem).join(" ")}`);
		originalConsoleError.apply(console, args);
	};
	window.addEventListener("error", onError);
	window.addEventListener("unhandledrejection", onRejection);
	process.on("unhandledRejection", onProcessRejection);

	let instance: ReturnType<typeof mount> | undefined;
	try {
		instance = mount(component as Component<Record<string, unknown>>, {
			target: options.target ?? document.body,
			props: options.props,
		});
		await settle();
	} catch (error) {
		if (instance) unmount(instance);
		throw error;
	} finally {
		console.error = originalConsoleError;
		window.removeEventListener("error", onError);
		window.removeEventListener("unhandledrejection", onRejection);
		process.off("unhandledRejection", onProcessRejection);
	}

	if (problems.length > 0) {
		unmount(instance);
		throw new Error(`mount reported errors:\n${problems.join("\n")}`);
	}
	const mountedInstance = instance;
	return { instance: mountedInstance, unmount: () => unmount(mountedInstance) };
}
